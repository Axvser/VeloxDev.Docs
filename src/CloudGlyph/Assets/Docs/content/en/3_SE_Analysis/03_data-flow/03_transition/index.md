# Data Flow — Transition

## (a) Normal execution flow

The complete call chain from `snapshot.Execute(target)` to the frame pump. This flow works identically across all six platform adapters.

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "InterpolatorCore" as IC
participant "UIThreadInspector" as UI
participant "FrameSequence" as FS
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

TC -> Sch: Execute(interpolator, state, effect, cts)
activate Sch

Sch -> IC: Interpolate(target, state, effect, isUIAccess, inspector)
activate IC

loop every recorded property
    IC -> UI: ProtectedGetValue(target, property)  (marshalled if needed)
    UI --> IC: currentValue
    alt custom interpolator (state.Interpolators)
        IC -> IC: customInterpolator.Interpolate(current, new, count, options)
    else registry TryGetInterpolator(propertyType)
        IC -> IC: interpolator.Interpolate(current, new, count, options)
    else IInterpolable on current or new value
        IC -> IC: value.Interpolate(current, new, count, options)
    end
    IC -> IC: output.AddPropertyInterpolations(property, frames)
end

IC --> Sch: FrameSequence (per-property frame lists, count = Duration/(1000/FPS))
deactivate IC

Sch -> TI: Execute(target, frameSequence, effect, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start event fired

loop index in 0 .. count-1
    TI -> TI: easedIndex = GetEaseIndex(effect.Ease, index, count)
    TI -> EF: InvokeUpdate(sender, args)
    TI -> FS: Update(target, easedIndex, priority)
    activate FS
    FS -> UI: ProtectedInvoke(target, setValues, priority)
    UI -> T: property.SetValue(target, frame[prop][easedIndex])
    deactivate FS
    TI -> EF: InvokeLateUpdate(sender, args)
    TI -> TI: await WaitForFrameAsync(stopwatch, frameMs, cts)
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

When `IsAutoReverse` or `LoopTime` is set, the interpreter wraps the frame walk. `LoopTime = int.MaxValue` loops forever.

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "FrameSequence" as FS
participant "Effect" as EF

TI -> TI: indexs = GetEaseIndex(effect.Ease, count)
TI -> TI: frameMs = Duration / count
TI -> EF: InvokeStart(sender, args)

loop loop in 0 .. effect.LoopTime (forever when int.MaxValue)
    loop index in 0 .. count-1  (forward walk)
        TI -> TI: cts/Args.Handled check
        TI -> EF: InvokeUpdate
        TI -> FS: Update(target, indexs[index], priority)
        TI -> EF: InvokeLateUpdate
        TI -> TI: await WaitForFrameAsync(frameMs)
    end
    alt effect.IsAutoReverse
        loop index in count-1 .. 0  (backward walk)
            TI -> TI: cts/Args.Handled check
            TI -> EF: InvokeUpdate
            TI -> FS: Update(target, indexs[index], priority)
            TI -> EF: InvokeLateUpdate
            TI -> TI: await WaitForFrameAsync(frameMs)
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

TI -> TI: frame loop
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

**App-shutdown path:** in `InterpolatorOutputBase.SetValues`, if `inspector.IsAppAlive() == false` (e.g. WinUI `DispatcherQueue` enqueue fails) the write is skipped; frames stop being applied without firing further events.

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
EX -> SA: Execute(interpolator, state, effect, cts)
SA -> SA: gate.WaitAsync() serializes; new mutual animation Exit()s the previous
SA -> T: apply frames (UI-marshalled)

EX -> NWT: CanMutualTask: false -> AddNoMutual(target, [scheduler])
EX -> SB1: Execute(...)
EX -> SB2: Execute(...)
SB1 -> T: apply frames in parallel
SB2 -> T: apply frames in parallel
SB1 -> NWT: RemoveNoMutual(target, [SB1]) on Completed
SB2 -> NWT: RemoveNoMutual(target, [SB2]) on Completed
@enduml
```

## Flow Summary

| Scenario | Behavior |
|---|---|
| Normal execution | Frames are pre-computed per property, then applied on the UI thread via `UIThreadInspector`; `Update`/`LateUpdate` events fire per frame; `Completed` + `Finally` at the end. |
| `IsAutoReverse` | After the forward walk, the interpreter walks frames backward (same eased index list). |
| `LoopTime` / `int.MaxValue` | The whole forward (+ reverse) walk repeats `LoopTime` times, or forever. |
| New mutual animation on same target | `CoreExecute` calls `scheduler.Exit()` before the new run; the previous scheduler cancels its current `cts`. |
| `TransitionEventArgs.Handled = true` | Throws `OperationCanceledException` → `Canceled` + `Finally`; timeline stops. |
| `Transition.Exit(target)` | Cancels the target's mutual (and optionally non-mutual) schedulers. |
| Background-thread start | `UIThreadInspector.ProtectedInvoke`/`ProtectedGetValue`/`ProtectedInterpolate` marshal to the UI thread. |
| Property without interpolator | The property is skipped (`UnreadablePath` sentinel or no registered interpolator); other properties still animate. |
| App shutting down | `IsAppAlive() == false` → frame writes skipped, no further events. |

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs` (frame pump, `GetEaseIndex`, `WaitForFrameAsync`), `TransitionScheduler.cs` (`FindOrCreate`, `Execute`, gate), `Interpolator.cs` (resolution), `InterpolatorOutputCore.cs` (`Update`/`SetValues`, cancellation skip), `StateSnapshot.cs` (`CoreExecute`), `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`.
