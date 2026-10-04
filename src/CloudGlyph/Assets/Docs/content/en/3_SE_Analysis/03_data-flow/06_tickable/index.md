# Data Flow — Tickable

The tickable feature has one call chain with three phases, and they are worth reading in order because each one changes the state the next one depends on:

1. **Start and registration** — the caller starts a channel and enqueues a behaviour; the update pump drains the queue before sampling, so `Awake` and `Start` land before the first `Update`.
2. **Frame delivery** — the steady state: one `Update` sweep, one `LateUpdate` sweep, and an independent `FixedUpdate` batch on the other thread.
3. **Pause, resume and stop** — the transitions that stop and restart delivery without tearing down the channel.

## The whole lifecycle in one picture

```plantuml
@startuml
!theme plain

actor Caller as Caller
participant "Tickable\n(user class)" as Beh
participant "TickManager\n(static facade)" as TM
participant "LoopChannel\n(private engine)" as Ch
participant "ITimeSourceControl\n(the bus)" as Bus
participant "Update pump\n(thread)" as UT
participant "FixedUpdate pump\n(thread)" as FT

== Start ==
Caller -> Beh: InitializeTickable()
activate Beh
Beh -> TM: RegisterBehaviour(this, "demo")
activate TM
TM -> Ch: GetOrCreateChannel("demo")
TM -> Ch: RegisterBehaviour(behavior)
Ch -> Ch: _addQueue.Enqueue(behavior)
deactivate TM
deactivate Beh

Caller -> TM: Start("demo")
activate TM
TM -> Ch: Start()
activate Ch
Ch -> Bus: Resume()
Ch -> Ch: _updateSampler.Reset() / _fixedSampler.Reset()
Ch -> Ch: RebuildCachedWrappers()
Ch -> UT: new Thread(UpdateLoop).Start()
Ch -> FT: new Thread(FixedUpdateLoop).Start()
Ch --> TM: Started
deactivate Ch
TM -> TM: OnChannelStarted?.Invoke(new TickChannelEventArgs("demo"))
deactivate TM

== Registration drain (update pump, before the first sample) ==
UT -> Ch: ProcessMainThreadOperations()
activate Ch
Ch -> Ch: ProcessAddedBehaviors()
Ch -> Beh: InvokeAwake()
Ch -> Beh: InvokeStart()
Ch -> Ch: _wrappersNeedSort = true
deactivate Ch

== Steady state ==
loop every frame until stopped
    UT -> Bus: IsAdvancing
    alt clock is stalled
        UT -> Bus: WaitWhileStalledAsync(token)
    else clock is advancing
        UT -> Ch: ProcessMainThreadOperations()
        UT -> Ch: _updateSampler.Sample()
        UT -> Beh: InvokeUpdate(frameArgs)
        alt Handled was set
            UT -> UT: break - skip the whole LateUpdate sweep
        end
        UT -> Beh: InvokeLateUpdate(frameArgs)
        UT -> Ch: _frameEventArgsPool.Return(frameArgs)
        UT -> Ch: FrameRateControlSync()
    end
end

loop every owed step, on its own thread
    FT -> Bus: IsAdvancing
    alt clock is stalled
        FT -> Bus: WaitWhileStalledAsync(token)
    else clock is advancing
        FT -> Ch: _fixedSampler.Advance(out sample)
        FT -> Beh: InvokeFixedUpdate(stepArgs) for each owed step
    end
end

== Pause and resume ==
Caller -> TM: Pause("demo")
activate TM
TM -> Ch: Pause()
Ch -> Bus: Pause()
Ch --> TM: Paused
TM -> TM: OnChannelPaused?.Invoke(...)
deactivate TM
note right of Bus: both pumps park here — IsAdvancing is now false

Caller -> TM: Resume("demo")
activate TM
TM -> Ch: Resume()
Ch -> Bus: Resume()
Ch --> TM: Resumed
TM -> TM: OnChannelResumed?.Invoke(...)
deactivate TM

== Stop ==
Caller -> TM: StopAsync("demo")
activate TM
TM -> Ch: StopAsync()
activate Ch
Ch -> Ch: _isRunning = false
Ch -> Bus: Resume()
Ch -> Ch: _cts.Cancel()
Ch -> UT: join (timeout 1000 ms)
Ch -> FT: join (timeout 1000 ms)
Ch -> Ch: ResetStatistics() / ClearQueues()
Ch --> TM: Stopped
deactivate Ch
TM -> TM: OnChannelStopped?.Invoke(...)
deactivate TM

@enduml
```

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 274-327 (Start), 329-374 (StopAsync), 384-402 (Pause/Resume), 430-438 (registration), 509-554 (UpdateLoop), 446-507 (FixedUpdateLoop), 753-801 (drain), 1017-1030 (GetOrCreateChannel), 1048-1064 (static forwards).

## Flows by phase

| Sub-page | Flow | Diagram |
|---|---|---|
| [Start and registration](00_start-and-registration/index.md) | `InitializeTickable()` → `RegisterBehaviour` → `GetOrCreateChannel` → `Start` → drain → `InvokeAwake`/`InvokeStart` | PlantUML |
| [Frame delivery](01_frame-delivery/index.md) | Per-frame `InvokeUpdate` → `InvokeLateUpdate`, the `Handled` short-circuit, the concurrent `InvokeFixedUpdate` batch, and the exception path | PlantUML |
| [Pause, resume and stop](02_pause-resume-and-stop/index.md) | `Pause` / `Resume` / `TogglePause` / `StopAsync` / `RestartAsync`, including the parked-pump and stop-while-paused paths | PlantUML |

## What crosses which boundary

The flow above is only meaningful if the thread boundaries are explicit. Every arrow in it crosses one of four boundaries:

| From → To | Mechanism | Consequence |
|---|---|---|
| Caller → `LoopChannel` | `ConcurrentQueue<T>` (add, remove, config) or a `volatile` field | Lock-free; applied later, not at the call |
| Update pump → behaviour | direct method call | Synchronous; a slow hook delays the frame |
| FixedUpdate pump → behaviour | direct method call, on its own thread | Concurrent with Update; shared state needs its own lock |
| Pump → bus | `ITimeSourceControl` | The pause and the rate are observed by both pumps and by any animation on the same clock |

The one thing that is **not** in this chain is any marshalling to a UI thread. `ExecuteOnMainThread` targets the update pump, and a hook that blocks on a `Dispatcher.Invoke` would be caught by the per-hook exception guard.
