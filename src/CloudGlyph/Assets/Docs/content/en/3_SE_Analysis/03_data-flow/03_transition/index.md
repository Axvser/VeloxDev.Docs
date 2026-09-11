# Data Flow — Transition

The engine is executed through the same core pipeline on every platform adapter. A run is **two-phase** inside each segment: first the scheduler *prepares* a normalized `SamplerSet` (reads current values, resolves samplers, fixes endpoints), then the interpreter drives a *continuous* Stopwatch-based sampling loop that marshals each frame write to the UI thread. This page shows the run lifecycle, the effect-scheduling loop, the UI-thread hop, and the scheduler fan-out/preemption rules.

## (a) Segment run lifecycle

`Execute(target)` walks the fluent builder chain (`root`…`next`), queues each segment's `(state, effect-clone, interpolator, delay)`, then plays them one at a time on a per-target scheduler. Cancellation is carried by one `CancellationTokenSource` shared across all segments of the run (registered with the scheduler for the whole run, including the `Await` gaps).

```plantuml
@startuml
!theme plain

actor "Caller" as Caller
participant "Transition<T> (builder)" as SS
participant "TransitionScheduler" as Sch
participant "UIThreadInspector" as UI
participant "InterpolatorCore" as IC
participant "SamplerSet" as SET
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target" as TGT

Caller -> SS: Execute(target, CanMutualTask)
activate SS

SS -> SS: Walk root -> next chain;\nqueue (interpolator, delay, effect-clone, state) per segment

SS -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch --> SS: shared scheduler cached in MutualSchedulers (ConditionalWeakTable)
else CanMutualTask == false
    Sch --> SS: fresh scheduler; registered in NoMutualSchedulers
end
opt CanMutualTask == true
    SS -> Sch: Exit()  (cancel the scheduler's active cts, if any -> new run preempts old)
end
deactivate Sch

loop one iteration per chained segment
    SS -> SS: await Task.Delay(segment.delay, cts)  (skip on OperationCanceledException)
    SS -> Sch: Execute(interpolator, state, effect, cts)
    activate Sch
    Sch -> Sch: _gate.WaitAsync()  (serialize executions on this scheduler)
    Sch -> UI: ProtectedInvokeAsync(target, () => effect.InvokeAwake(target, args))
    activate UI
    UI -> EF: Awaked event (raised on the UI thread; the scheduler awaits it)
    UI --> Sch
    deactivate UI

    Sch -> IC: Prepare(target, state, effect, inspector)
    activate IC
    loop every recorded property
        IC -> UI: ProtectedGetValue(target, property)  (marshal the read if off-thread)
        UI --> IC: current value (start)
        IC -> IC: resolve sampler: state override -> registry -> value-type ISampleable (StructAssembler)
        IC -> IC: normStart = NormalizeStart(cur, new, opt);\nnormEnd = NormalizeEnd(cur, new, opt)
        IC -> SET: Add(property, sampler, normStart, normEnd, options)
    end
    IC --> Sch: SamplerSet (one entry per property)
    deactivate IC

    alt cts cancelled or Args.Handled set by Awake
        Sch --> SS: run skipped (no sampling)
    else
        Sch -> TI: Execute(target, samplerSet, effect, cts)
        activate TI
        TI -> TI: Start/Update/Apply/LateUpdate ... Completed\n(b: sampling loop)
        TI --> Sch: completed
        deactivate TI
    end
    Sch -> Sch: finally: release _gate; clear cts
    Sch --> SS
    deactivate Sch
end

SS --> Caller: return
deactivate SS
@enduml
```

Sources: `TransitionSystem/Transition.cs` (`CoreExecute`, segment queueing and play loop), `TransitionScheduler.cs` (`FindOrCreate`, `Execute`, `_gate`, weak target reference), `Interpolator.cs` (`Prepare`, sampler resolution), `SamplerSet.cs`.

## (b) Effect scheduling and the sampling loop

Each segment's interpreter runs one continuous loop. `Duration`/`FPS` come from the segment's `Effect`; `FPS` is a **maximum sample-rate cap** — the yield interval is `1000 / FPS` ms, while the Stopwatch is the only timing source (so `Task.Delay` imprecision never skews the animation). `LoopTime = int.MaxValue` loops forever.

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start fired
TI -> TI: frameSet.SetCancellation(cts);\ndurationMs = effect.Duration.TotalMilliseconds
TI -> TI: sampleIntervalMs = 1000 / max(1, effect.FPS)\nforeverloop = (effect.LoopTime == int.MaxValue)
TI -> TI: stopwatch = Stopwatch.StartNew(); cycle = 0

loop while (foreverloop || cycle <= effect.LoopTime)
    loop forward pass until rawT >= 1
        TI -> TI: throw OperationCanceledException if cts cancelled or Args.Handled
        TI -> TI: rawT = (stopwatch.Elapsed - passStartMs) / durationMs
        TI -> TI: easedT = rawT >= 1 ? 1 : clamp(effect.Ease.Ease(rawT), 0, 1)
        TI -> EF: InvokeUpdate(sender, args)
        TI -> TI: apply(easedT) -> SamplerSet.Apply (UI-thread hop, see (c))
        TI -> EF: InvokeLateUpdate(sender, args)
        TI -> TI: await Task.Delay(sampleIntervalMs, cts)\n(Stopwatch is the timing authority)
    end
    opt effect.IsAutoReverse
        loop backward pass until rawT >= 1
            TI -> TI: throw OperationCanceledException if cts cancelled or Args.Handled
            TI -> TI: easedT = rawT >= 1 ? 0 : clamp(effect.Ease.Ease(1 - rawT), 0, 1)
            TI -> EF: InvokeUpdate / apply(easedT) / InvokeLateUpdate
        end
    end
end
TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed fired
TI -> EF: InvokeFinally(sender, args)
EF --> TI: Finally fired
@enduml
```

Each pass writes an **exact endpoint** on its last sample (`forward → easedT = 1`, `reverse → easedT = 0`) rather than relying on `Ease(1)`; each sampler maps `t <= 0` / `t >= 1` to the exact normalized start/end value.

## (c) UI-thread hop, cancellation, and app-shutdown guard

`SamplerSet.Apply` reuses one cached closure per target and hands the current eased time to the UI thread via `ProtectedInvoke`. If the target's dispatcher is the current thread the write runs inline; otherwise it is posted to the target's dispatcher. Reads during `Prepare` are marshaled the same way by `ProtectedGetValue`. A cancelled run or a dead app skips queued writes (the "stale-frame guard"), so a reset/exit result is never overwritten.

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "SamplerSet" as SET
participant "UIThreadInspector" as UI
participant "ISampler" as SM
participant "Target" as TGT
participant "Effect" as EF

TI -> SET: Apply(target, easedT, priority)
activate SET
alt cts.IsCancellationRequested
    SET --> TI: return (skip stale queued frame)
else not CanSetValue()  (inspector.IsAppAlive() == false)
    SET --> TI: return (no write, no further events)
else
    SET -> UI: ProtectedInvoke(target, cachedApply, priority)
    activate UI
    UI -> UI: CheckAccess()? run inline\nelse dispatch to the target's owning dispatcher
    UI -> SM: InsertFrame(target, property, ref working, start, end, options, t)
    SM -> TGT: write value (t <= 0/t >= 1 -> exact start/end)
    UI --> SET
    deactivate UI
    SET --> TI: return
end
deactivate SET

== Cancellation / short-circuit inside the sampling loop ==

TI -> TI: cts cancelled (Transition.Exit / preempting new mutual run)\nor Args.Handled == true (an event handler killed the timeline)
TI -> TI: throw OperationCanceledException
TI -> EF: InvokeCancled(sender, args)
EF --> TI: Canceled fired
TI -> EF: InvokeFinally(sender, args)
EF --> TI: Finally fired (non-mutual runs also unregister from NoMutualSchedulers here)
TI -> TI: stop immediately
@enduml
```

Sources: `TransitionSystem/SamplerSet.cs` (`Apply`, `SetCancellation`, `CanSetValue`, cached apply closure), `TransitionInterpreter.cs` (`ExecuteSamplingLoopAsync`, `RunPassAsync`), `TransitionEffect.cs` (event invocation), `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs` (per-platform marshaling).

## (d) Scheduler selection, preemption, and fan-out

One target holds **at most one** shared mutual scheduler (serialized by a `SemaphoreSlim`) but can run **many** concurrent non-mutual schedulers. A new mutual run on the same target preempts (cancels) the one currently executing.

```mermaid
flowchart TD
    A[Call transition.Execute target, CanMutualTask] --> B{CanMutualTask?}
    B -->|true| C[FindOrCreate returns the shared scheduler from MutualSchedulers CWT]
    C --> D[Exit current run - cancel every tracked cts, bump the generation]
    D --> E[New cts; track it for the whole run; queue all chained segments]
    B -->|false| F[Allocate a fresh scheduler; AddNoMutual registers it under NoMutualSchedulers]
    F --> E
    E --> G[For each segment: await delay, then scheduler.Execute]
    G --> G2{Generation changed while queued?}
    G2 -->|yes - an Exit landed| Z[Give up without running]
    G2 -->|no| H{Acquire _gate?}
    H -->|no - previous Execute still running| G
    H -->|yes| I[Await Awake on UI thread, Prepare SamplerSet]
    I --> J[Interpreter sampling loop]
    J --> K{End of segment?}
    K -->|cancelled / Handled| L[InvokeCancled + InvokeFinally; release gate]
    K -->|loop exhausted| M[InvokeCompleted + InvokeFinally; release gate]
    L --> N[After the last segment: untrack cts; non-mutual unregister from NoMutualSchedulers]
    M --> N
```

`Transition.Exit(target, IncludeMutual, IncludeNoMutual)` cancels the target's mutual scheduler and, optionally, every running non-mutual scheduler; those schedulers then unwind through the `Canceled`/`Finally` path above.

Scheduler selection is *not* part of the builder's type arguments: `Transition<T>` is `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>`, and `CoreExecute` resolves the scheduler internally through `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>.FindOrCreate`. (Avalonia and WinUI additionally declare their adapter scheduler as the generic `TransitionScheduler<TTarget>`; its type parameter is unused.)

## Flow Summary

| Scenario | Behavior |
|---|---|
| Normal run | `CoreExecute` queues every chained segment, then per segment: `await delay` → scheduler `Execute` (gate) → `Awake` on UI thread → `Prepare` builds one `SamplerSet` entry per property → interpreter samples continuously (`t = eased elapsed/duration`) and applies each frame on the UI thread → `Completed` + `Finally`. |
| `IsAutoReverse` | After the forward pass the interpreter runs a backward pass (same samplers; pass end `easedT = 0`). |
| `LoopTime` / `int.MaxValue` | The whole forward (+ reverse) pair repeats `LoopTime + 1` times (`cycle <= LoopTime`, `cycle` from 0), or forever. |
| Segment `Await` delay | A pre-delay per segment (`CoreAwait`/`CoreAwaitThen`); skipped on cancellation (`OperationCanceledException`). |
| New mutual run on the same target | `CoreExecute` drains and cancels the previous run's tokens first (bumping the generation); the previous run gives up at its next check, so queued frames are skipped. |
| `TransitionEventArgs.Handled = true` | An event handler throws `OperationCanceledException` → `Canceled` + `Finally`; the timeline stops. |
| `Transition.Exit(target, …)` | Cancels the target's mutual (and optionally non-mutual) schedulers; each tracked token of a run is cancelled at once, and the run unregisters itself in its own `finally`. |
| Started on a background thread | `UIThreadInspector` marshals reads (`ProtectedGetValue`) and frame writes (`ProtectedInvoke`) to the target's UI thread; lifecycle events still run on the interpreter's execution thread (only `Awake` and frame writes are always on the UI thread). |
| Property without a sampler / invalid path | A path that does not match the target's runtime type is skipped in `Prepare` (`UnreadablePath` sentinel from the compiled getter); a declared **reference-type** path with no sampler at all is rejected by `Execute` (`TransitionPathUnsampleableException`) instead of animating nothing. Other properties keep animating. |
| App shutting down | `SamplerSet.CanSetValue()` returns false → `Apply` skips the write and fires no further events. |

> Sources: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionScheduler.cs` (gate, CWT tables, weak target, generation/drain), `TransitionInterpreter.cs` (`ExecuteSamplingLoopAsync`/`RunPassAsync`), `SamplerSet.cs` (`Apply` + cancellation/app-alive guard), `Interpolator.cs` (`Prepare`), `Transition.cs` (`CoreExecute`), `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`.

Related analysis: [Design patterns — Transition](../../02_design-patterns/03_transition/index.md) · [Complexity — Transition](../../04_complexity/03_transition/index.md)
