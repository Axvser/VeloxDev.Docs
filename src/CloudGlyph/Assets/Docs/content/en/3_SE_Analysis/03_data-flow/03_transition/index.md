# Data Flow — Transition

## (a) Normal execution flow

The complete call chain from `snapshot.Execute(target)` to the Stopwatch-driven sampling loop. This flow works identically across all six platform adapters.

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "InterpolatorCore" as IC
participant "UIThreadInspector" as UI
participant "SamplerSet" as FUS
participant "ISampler" as SM
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target (UI element)" as T

User -> SS: Execute(Rec0, CanMutualTask)
activate SS

SS -> TC: (static) Execute(target, snapshot, CanMutualTask)
activate TC

TC -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch -> Sch: return shared mutual scheduler (ConditionalWeakTable)
else CanMutualTask == false
    Sch -> Sch: return one-off non-mutual scheduler
end
Sch --> TC: scheduler
deactivate Sch

TC -> Sch: Execute(producer, state, effect, cts)
activate Sch

Sch -> IC: Prepare(target, state, effect, inspector)
activate IC

loop every recorded property
    IC -> UI: ProtectedGetValue(target, property)  (marshalled if needed)
    UI --> IC: currentValue (start)
    alt custom sampleable (state.Interpolators)
        IC -> IC: sampleable = state.Interpolators[property]
    else registry TryGetInterpolator(propertyType)
        IC -> IC: sampleable = NativeInterpolators[type]
    else current/new value is ISampleable
        IC -> IC: sampleable = value
    end
    IC -> IC: sampler = sampleable.Normalize(current, new, options)
    IC -> FUS: Add(property, sampler, start, end, options)
end

IC --> Sch: SamplerSet (one prepared sampler entry per property)
deactivate IC

Sch -> TI: Execute(target, samplerSet, effect, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start event fired

loop each pass (forward; backward when IsAutoReverse)
    loop sample until rawT >= 1 (Stopwatch-driven)
        TI -> TI: rawT = elapsed / durationMs  (clamped to [0,1])
        TI -> TI: easedT = Ease(rawT), clamped to [0,1]
        TI -> EF: InvokeUpdate(sender, args)
        TI -> FUS: Apply(target, easedT, priority)
        activate FUS
        FUS -> UI: ProtectedInvoke(target, applyCore, priority)\n(skipped if cancelled / app dead)
        UI -> SM: Update(target, property, start, end, options, easedT)
        SM -> T: t<=0 → exact start / t>=1 → exact end /\nmiddle → SetValue (value) or in-place mutation (reference)
        deactivate FUS
        TI -> EF: InvokeLateUpdate(sender, args)
        TI -> TI: await Task.Delay(1)  (coarse yield only; Stopwatch is the timing source)
    end
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
deactivate TI
Sch --> TC: completed
deactivate Sch
TC --> SS
deactivate TC
SS --> User: return
deactivate SS
@enduml
```

## (b) Auto-reverse / loop flow

When `IsAutoReverse` or `LoopTime` is set, the interpreter wraps the sampling passes. `LoopTime = int.MaxValue` loops forever.

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "SamplerSet" as FUS
participant "Effect" as EF

TI -> TI: durationMs = effect.Duration.TotalMilliseconds
TI -> TI: stopwatch = Stopwatch.StartNew()
TI -> EF: InvokeStart(sender, args)

loop loop in 0 .. effect.LoopTime (forever when int.MaxValue)
    loop forward pass (sample until rawT >= 1)
        TI -> TI: cts/Args.Handled check
        TI -> TI: rawT = stopwatch.Elapsed / durationMs
        TI -> TI: easedT = clamp(Ease(rawT), 0, 1)
        TI -> EF: InvokeUpdate
        TI -> FUS: Apply(target, easedT, priority)
        TI -> EF: InvokeLateUpdate
        TI -> TI: await Task.Delay(1)  (coarse yield)
    end
    alt effect.IsAutoReverse
        loop backward pass (sample until rawT >= 1)
            TI -> TI: cts/Args.Handled check
            TI -> TI: easedT = clamp(Ease(1 - rawT), 0, 1); endpoint easedT = 0
            TI -> EF: InvokeUpdate
            TI -> FUS: Apply(target, easedT, priority)
            TI -> EF: InvokeLateUpdate
            TI -> TI: await Task.Delay(1)  (coarse yield)
        end
    end
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
@enduml
```

## (c) Cancellation / `TransitionEventArgs.Handled = true` short-circuit

A cancelled `cts` (from `Transition.Exit` or a new mutual animation) or a handler setting `Handled = true` throws `OperationCanceledException`; the interpreter fires `Canceled` + `Finally` and stops.

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "TransitionEventArgs" as Args

TI -> TI: sampling loop
TI -> Args: Args.Handled read
alt Args.Handled == true  (event handler short-circuit)
    TI -> TI: throw OperationCanceledException
else cts.IsCancellationRequested (Transition.Exit / new mutual)
    TI -> TI: throw OperationCanceledException
end
TI -> EF: InvokeCancled(sender, args)
EF --> TI: Canceled event fired
TI -> EF: InvokeFinally(sender, args)
EF --> TI: Finally event fired
TI -> TI: stop immediately
@enduml
```

**App-shutdown path:** `SamplerSet.Apply` checks `inspector.IsAppAlive()` (via `CanSetValue`); when it is `false` (e.g. WinUI `DispatcherQueue` enqueue fails) the write is skipped. The same guard inside `ApplyCore` stops mid-pass, so samples stop being applied without firing further events. Cancelled animations (`cts.IsCancellationRequested`) skip their queued writes the same way — the former `ICancellableFrameSequence` stale-frame guard.

## (d) Mutual vs non-mutual scheduler fan-out

One target holds **at most one** shared mutual scheduler (serialized by a `SemaphoreSlim`) but **many** concurrent non-mutual schedulers.

```plantuml
@startuml
!theme plain

participant "StateSnapshot.Execute" as EX
participant "Target" as T
participant "MutualSchedulers (CWT)" as MWT
participant "NoMutualSchedulers (CWT)" as NWT
participant "Scheduler (mutual, shared)" as SA
participant "Scheduler (non-mutual #1)" as SB1
participant "Scheduler (non-mutual #2)" as SB2

EX -> MWT: CanMutualTask: true -> FindOrCreate(target)
MWT --> EX: shared scheduler (1 per target)
EX -> SA: Execute(producer, state, effect, cts)
SA -> SA: gate.WaitAsync() serializes; new mutual animation Exit()s the previous
SA -> T: apply updater writes (UI-marshalled)

EX -> NWT: CanMutualTask: false -> AddNoMutual(target, [scheduler])
EX -> SB1: Execute(...)
EX -> SB2: Execute(...)
SB1 -> T: apply updater writes in parallel
SB2 -> T: apply updater writes in parallel
SB1 -> NWT: RemoveNoMutual(target, [SB1]) on Completed
SB2 -> NWT: RemoveNoMutual(target, [SB2]) on Completed
@enduml
```

## Flow Summary

| Scenario | Behavior |
|---|---|
| Normal execution | `InterpolatorCore.Prepare` resolves one per-property `ISampleable` and calls `Normalize` (reads current=start, target=end), storing a per-property `(property, sampler, start, end, options)` entry; the interpreter samples continuously with a Stopwatch (`t = elapsed/duration`, eased + clamped) and applies via `SamplerSet.Apply`, marshalled to the UI thread; `Update`/`LateUpdate` events fire per sample; `Completed` + `Finally` at the end. |
| `IsAutoReverse` | After the forward pass, the interpreter runs a backward pass (same samplers; the endpoint `easedT` is forced to 0). |
| `LoopTime` / `int.MaxValue` | The whole forward (+ reverse) pass repeats `LoopTime` times, or forever. |
| New mutual animation on same target | `CoreExecute` calls `scheduler.Exit()` before the new run; the previous scheduler cancels its current `cts`. |
| `TransitionEventArgs.Handled = true` | Throws `OperationCanceledException` → `Canceled` + `Finally`; timeline stops. |
| `Transition.Exit(target)` | Cancels the target's mutual (and optionally non-mutual) schedulers. |
| Background-thread start | `UIThreadInspector.ProtectedInvoke`/`ProtectedGetValue` marshal reads and writes to the UI thread. |
| Property without a sampler | The property is skipped in `Prepare` (`UnreadablePath` sentinel or no resolved `ISampleable`); other properties still animate. |
| App shutting down | `SamplerSet.CanSetValue()` checks `IsAppAlive()` → writes skipped, no further events. |

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs` (Stopwatch-driven sampling loop, `ExecuteSamplingLoopAsync`), `TransitionScheduler.cs` (`FindOrCreate`, `Execute`, gate), `Interpolator.cs` (`Prepare`, sampler resolution), `SamplerSet.cs` (`Apply`, cancellation/app-alive skip), `StateSnapshot.cs` (`CoreExecute`), `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`.
