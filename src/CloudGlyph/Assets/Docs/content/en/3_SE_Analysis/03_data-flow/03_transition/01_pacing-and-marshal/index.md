# Data Flow — Transition: Pacing & Marshaling

Two things happen per frame: the loop decides *when* to sample (pacing), and each sample's values are written on the target's own thread (marshaling). They are separate concerns with separate failure modes, which is why they are drawn separately.

## (a) One pass: timeline-driven sampling

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "FramePacerCore\n(host pacer or none)" as PACER
participant "ReusableTimerWait\n(default wait)" as WAIT
participant "Run" as RUN
participant "Timeline\n(ITimeSourceControl)" as TL
participant "Effect" as EF

TI -> EF: InvokeStart(sender, args)  (once per run)
TI -> TI: run = frameSet.Run\nforeverloop = (LoopTime == int.MaxValue)\nstartCycle = run.Cycle

note over TI
  The run and the start-cycle offset are what make a
  segment's loop its OWN: a second segment in a chain
  begins with the shared counter already advanced.
end note

loop while foreverloop or run.Cycle - startCycle <= LoopTime
    TI -> RUN: PassAnchor = Timeline.Ticks  (an anchor, not a reset)
    loop forward pass until rawT >= 1
        alt cts cancelled or Args.Handled
            TI -> TI: throw OperationCanceledException
        else timeline is not advancing
            TI -> TI: draw the frozen position ONCE
            TI -> TL: await WaitWhileStalledAsync(cts.Token)
            note right of TI
              Draw-then-park is what makes a seek while paused
              visible without resuming: the wait is replaced by
              a nudge, so the loop wakes, draws and parks again.
              A plain pause therefore costs one frame and then
              NO timer wake-ups at all.
            end note
        else
            TI -> TL: elapsedTicks = Ticks - PassAnchor
            TI -> TI: rawT = TicksToMs(elapsedTicks) / durationMs\neasedT = rawT >= 1 ? 1 : Ease.Ease(rawT)
            TI -> EF: InvokeUpdate
            TI -> TI: apply(easedT)  into SamplerSet.Apply  (see part b)
            TI -> EF: InvokeLateUpdate
            alt host supplied a pacer
                TI -> PACER: Schedule(continuation, 1000 / max(1, FPS) ms, token)
            else
                TI -> WAIT: Schedule(continuation, 1000 / max(1, FPS) ms, token)
            end
            note over TI, WAIT
              Interval is re-read per frame, so raising FPS mid-animation
              tightens the cap. The interval only caps how OFTEN the loop
              looks; the timeline decides how FAR the frame is.
            end note
        end
    end
    opt IsAutoReverse
        loop backward pass until rawT >= 1
            TI -> TI: easedT = rawT >= 1 ? 0 : Ease.Ease(1 - rawT)
        end
    end
    TI -> RUN: NextCycle()
end
TI -> EF: InvokeCompleted(sender, args)
TI -> EF: InvokeFinally(sender, args)
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs` (`ExecuteSamplingLoopAsync`, `RunPassAsync`, `EmitFrame`, `ArmNextFrame`), `FramePacerCore.cs`, `ReusableTimerWait.cs`, `TransitionRun.cs`.

The load-bearing line is `Pacer.PassAnchor = Timeline.Ticks`. A pass is an **anchor** into an absolute timeline, never a reset — so several runs can share one source (each keeps its own pass and its own place), and `Transition.Seek` is nothing more than writing a different anchor. Two consequences the diagram shows: the pass ends in exactly one place (its far end), because the timeline only ever moves forwards; and the last frame of a pass is the **exact** endpoint (`easedT = 1` forward, `0` reverse), independent of whether `Ease(1)` is exactly `1`.

`FPS` is worth restating: it is a *cap*, not a grid. `ArmNextFrame` re-reads `1000 / max(1, FPS)` every frame, so tightening the cap on a running animation takes effect immediately; waking late just draws a frame further along.

## (b) The wait: host pacer, else one reused timer

```plantuml
@startuml
!theme plain

participant "Interpreter" as TI
participant "FramePacerCore" as P
participant "Host timer\n(DispatcherTimer etc.)" as T
participant "ReusableTimerWait" as W
participant "Timer\n(thread pool)" as TP

TI -> TI: ArmNextFrame(continuation, interval, token)
alt token already cancelled
    TI -> TI: run the continuation now (a stop costs no interval)
else the host resolved a pacer on the first frame
    TI -> P: Schedule(continuation, interval, token)
    activate P
    P -> P: Volatile.Write(_pending, continuation)  -- BEFORE arming
    P -> T: Arm(interval)   (subclass hook)
    activate T
    T --> P: tick  ->  pacer.Fire()
    deactivate T
    P -> P: Disarm() first, then Interlocked.Exchange(_pending, null)
    P --> TI: continuation runs ON the host's thread
    deactivate P
else
    TI -> W: Schedule(continuation, interval, token)
    activate W
    W -> W: bind the token once for the whole loop
    W -> TP: Change(interval, infinite)
    activate TP
    TP --> W: callback  ->  Fire()
    deactivate TP
    W --> TI: continuation runs on a thread-pool thread
    deactivate W
end

note over P, W
  Publishing before arming, and disarming before invoking,
  are both ordering constraints: an already-expired timer must
  not tick before the continuation is attached, and a repeating
  wait must not complete again before the loop armed the next frame.
end note
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/{FramePacerCore,ReusableTimerWait,TransitionInterpreter}.cs`, `Src/Adapters/*/PlatformAdapters/TransitionInterpreter.cs`.

Why a custom awaiter is not marshalled back: `FrameWait` implements `INotifyCompletion` and deliberately **not** `ICriticalNotifyCompletion`, so the builder flows the caller's `ExecutionContext` — but restoring a `SynchronizationContext` is `Task`'s job, so a custom awaiter's continuation resumes on whatever thread completed the wait. A loop started on a UI thread therefore drifts to a pool thread after its first frame *unless the host supplied a pacer*. That is the whole reason the pacing seam exists, and why a host must derive its pacer from the same answer the write path uses: a pacer that disagrees with `Post` turns every frame into a dispatch.

## (c) The UI-thread hop

```plantuml
@startuml
!theme plain

participant "Interpreter" as TI
participant "SamplerSet" as SET
participant "Host\n(ITransitionHost)" as H
participant "ISampler" as SM
participant "Target" as TGT

TI -> SET: Apply(target, easedT, priority)
activate SET
alt cts.IsCancellationRequested
    SET --> TI: return  (a stale queued frame is discarded)
else host.IsAlive is false
    SET --> TI: return  (no write, no further frames)
else
    SET -> SET: resolve the thread the RUN is pinned to\n(fall back to host.ThreadFor(target) with no run)
    SET -> H: Post(target, thread, cachedApply, priority)
    activate H
    alt the caller is already on that thread
        H -> H: RunInline(cachedApply)   -- no dispatch at all
    else
        H -> H: PostCore(target, thread, action, priority)
        note right of H
          Returns false when nothing was queued at all
          (dispatcher gone, or no queue yet). That is the only
          way a caller can tell a dropped action from a queued one,
          and it is reported once through Warn(WarnStage.Dropped).
        end note
    end
    H -> SM: InsertFrame(target, property, ref working, start, end, options, t)
    SM -> TGT: write the value (endpoints written exactly)
    deactivate H
    note right of SET
      The cancellation and liveness checks are repeated inside
      the queued write, so a frame that landed after a reset
      is discarded too.
    end note
    SET --> TI: return
end
deactivate SET
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/SamplerSet.cs` (`Apply`, `ApplyCore`, cached closure, `SetRun`), `Src/Core/VeloxDev.Core/Threading/ThreadDispatcherBase.cs`, `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`.

Three allocation-avoidance decisions are visible in this flow:

- **The eased time travels in a field, not a closure.** `Apply` keeps one cached `Action` per target and stores `t` with `Interlocked.Exchange(ref _cachedTimeBits, BitConverter.DoubleToInt64Bits(t))`, so per-sample marshaling allocates nothing.
- **The thread is not re-derived per frame.** A run pins its `ThreadRef` once, when the scheduler starts it, because the write path runs on the sampling loop's thread and that thread carries no answer for a host whose answer depends on the caller — a Blazor circuit's renderer cannot be named from there.
- **The check is repeated inside the queued write.** `ApplyCore` re-checks the token and the liveness flag, because the write happens when the message is pumped and the animation can be cancelled in between; checking only before queueing would let an already-stale frame overwrite a reset.
