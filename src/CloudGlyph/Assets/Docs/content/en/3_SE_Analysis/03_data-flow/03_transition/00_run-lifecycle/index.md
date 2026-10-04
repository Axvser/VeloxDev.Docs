# Data Flow — Transition: Run Lifecycle

One `Execute` call, from the fluent builder to the last frame. The distinctive step is `Prepare`: the interpreter never touches the declared state, only the `SamplerSet` that `Prepare` produced, and that set is what "a state snapshot" means in this engine — one entry per declared path, each holding its sampler plus the two **normalized endpoint values**.

## (a) One run, one segment

```plantuml
@startuml
!theme plain

actor "Caller" as Caller
participant "Transition<T>\n(builder + chain)" as SS
participant "TransitionScheduler" as Sch
participant "Host\n(ITransitionHost)" as Host
participant "InterpolatorCore" as IC
participant "SamplerSet" as SET
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target" as TGT

Caller -> SS: Execute(target, CanMutualTask)
activate SS

SS -> SS: walk root -> next;\nqueue (interpolator, delay, effect-clone, state) per segment
SS -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch --> SS: the shared scheduler from MutualSchedulers (per-target cache)
    SS -> Sch: DrainActive()  (supersede the running mutual run)
else CanMutualTask == false
    Sch --> SS: a fresh scheduler, registered in NoMutualSchedulers
end
deactivate Sch

SS -> SS: new TransitionRun(runSource)\nTrack(run); add no-mutual registration if concurrent
SS -> Sch: Execute(interpolator, state, effect, cts)
activate Sch
Sch -> Sch: await _gate  (serialize executions on this scheduler)
Sch -> Host: PostAsync(target, () => effect.InvokeAwake(target, args))
activate Host
Host -> EF: Awaked
Host --> Sch: accepted true, or false when the queue refused it
deactivate Host

note right of Sch
  Awake is awaited, not fired and forgotten:
  it may veto the run (Args.Handled) and may put
  the target into the state the segment starts from,
  so Prepare must not read the target until it has run.
  A refused dispatch aborts here with a Warn.
end note

Sch -> IC: Prepare(target, state, effect, host)
activate IC
loop every declared path
    IC -> IC: bound = property.BindTo(target)  (freeze PathIndex.Frozen args)
    IC -> Host: Run(target, () => bound.GetValue(target))
    activate Host
    Host --> IC: current value, or TransitionProperty.UnreadablePath
    deactivate Host
    IC -> IC: resolve sampler:\nstate override -> registry (exact, base classes, interfaces)\n-> struct ISampleable (StructAssembler)
    IC -> IC: normStart = NormalizeStart(cur, new, opt)\nnormEnd = NormalizeEnd(cur, new, opt)
    IC -> SET: Add(bound, sampler, normStart, normEnd, options)
end
IC --> Sch: SamplerSet (one entry per path)
deactivate IC

alt Awake vetoed, cts cancelled, or the generation changed
    Sch --> SS: no sampling
else
    Sch -> SET: SetRun(run)   (timeline + pass the frames are positioned against)
    Sch -> TI: Execute(target, samplerSet, effect, cts)
    activate TI
    TI -> TI: sampling loop  (see the pacing page)
    TI --> Sch: completed or cancelled
    deactivate TI
end
Sch -> Sch: finally: release _gate
Sch --> SS: return the frame set (ExecuteCapturing) or nothing (Execute)
deactivate Sch

SS -> SS: finally (after the last segment):\nUntrack(run); remove no-mutual registration; run.Dispose()
SS --> Caller: return (the call returns before the animation finishes)
deactivate SS
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs` (`CoreExecute`, `ExecuteCoreAsync`, `RunSegmentAsync`), `TransitionScheduler.cs` (`FindOrCreate`, `ExecuteCore`, gate, generation, `Track`/`Untrack`), `Interpolator.cs` (`Prepare`), `SamplerSet.cs`.

## (b) What a prepared state is

`Prepare` is the only place a target is read. Everything downstream works from the resulting `SamplerSet<TPriorityCore>`, whose entries are exactly `(property, sampler, normalizedStart, normalizedEnd, options)` plus a lazily-created `working` scratch:

```plantuml
@startuml
!theme plain

participant "CoreExecute" as SS
participant "Prepare" as P
participant "state (IFrameState)" as ST
participant "SamplerSet" as SET
participant "Interpreter" as TI

SS -> P: Prepare(target, state, effect, host)
activate P
P -> P: diagnostics = new TransitionDiagnostics(effect, target)
loop path p in state.Values
    alt state.Interpolators holds p
        P -> P: sampler = the per-property override
    else registry resolves p.PropertyType
        P -> P: sampler = TryGetInterpolator(p.PropertyType)
    else p is a value type implementing ISampleable
        P -> P: sampler = StructAssembler.Create(...)  (null means skip)
    else
        P -> P: Warn(WarnStage.Unsampled) and skip this path
    end
    P -> ST: TryGetOptions(p)
    ST --> P: options (e.g. RotationDirection)
    P -> P: normStart = sampler.NormalizeStart(cur, new, options)\nnormEnd = sampler.NormalizeEnd(cur, new, options)
    P -> SET: Add(property, sampler, normStart, normEnd, options)
end
P --> SS: the set
deactivate P
SS -> TI: Execute(target, set, effect, cts)
activate TI
TI -> SET: Apply(target, easedT, priority)   per frame
activate SET
SET -> SET: skip when cancelled or the host is dead
SET --> TI: (each entry writes through its sampler)
deactivate SET
deactivate TI
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs` (`Prepare<TPriorityCore>`), `SamplerSet.cs` (`Add`, `Apply`, `CanSetValue`), `StructAssembler.cs`.

Three facts about the set that make the rest of the engine simple:

- **It is fixed for the run.** The declared values and the samplers are resolved once; a frame never re-reads the state, re-parses a path or re-resolves a type. That is why `Repeat` can *replay* the set it prepared on the first iteration and get an identical animation each time.
- **The endpoints are already normalized.** `NormalizeStart` / `NormalizeEnd` ran once with the start value, the end value and the options; the frame path only ever evaluates an eased time against them.
- **A path that cannot be prepared is skipped, not fatal.** `UnreadablePath` (the path does not match this target's runtime type) and "no sampler resolves" both produce a `Warn` and a missing entry — the rest of the set still animates. `null` from `StructAssembler` is the same outcome. The one case that *is* fatal happens earlier, synchronously in `Execute`: a declared reference-type path for which nothing resolves throws `TransitionPathUnsampleableException`.

## (c) Segment chaining and loops

```plantuml
@startuml
!theme plain

participant "CoreExecute" as SS
participant "DelayWhilePausedAsync" as D
participant "Scheduler\n(chainScheduler)" as Sch
participant "prepared[]" as PP

SS -> SS: segments[] and repeats[] built by walking root -> next
SS -> SS: prepared[] = new SamplerSet[segments.Count]

note over SS
  RunRangeAsync(from, to) expands the loop of segment `to`
  (a segment's loop wraps the chain from its FIRST segment
  through that one, and loops nest by where they end)
end note

loop for each iteration of the innermost loop, innermost last
    SS -> D: DelayWhilePausedAsync(run.Timeline, segment.Delay, cts)
    activate D
    D -> D: park while paused; measure the delay on the WALL clock
    D --> SS: delay consumed, or OperationCanceledException
    deactivate D
    alt prepared[i] is null   (first iteration of this segment)
        SS -> Sch: ExecuteCapturing(interpolator, state, effect, cts)
        activate Sch
        Sch --> SS: the ready SamplerSet, stored into prepared[i]
        deactivate Sch
    else
        SS -> Sch: Replay(prepared[i], effect, cts)
        note right of Sch
          A replay re-reads nothing and re-raises no Awake;
          Start / Update / LateUpdate / Completed and the
          diagnostics still fire, exactly like a pass.
        end note
    end
end

SS -> SS: finally: Untrack(run); remove the no-mutual registration; run.Dispose()
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs` (`RunSegmentAsync`, `RunBodyAsync`, `RunRangeAsync`, `DelayWhilePausedAsync`), `TransitionScheduler.cs` (`ExecuteCapturing`, `Replay`).

The delay between segments is measured on the **wall clock** (a `Stopwatch`), not on the source: a rate of zero freezes the source without pausing it (`IsPaused` stays false), and a delay measured on a frozen clock would never decrease. The sampling loop does the opposite on purpose — it uses the timeline, because there the timeline is what decides how far the animation has gone.
