# Data Flow — MonoBehaviour

The frame loop is driven by one Update thread and one FixedUpdate thread per channel (or two async tasks when `UseAsyncLoop` is `true`). Config, registration and main-thread actions are exchanged through concurrent queues drained at the start of each frame.

## 1. Channel start and per-frame dispatch

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update thread" as U
participant "FixedUpdate thread" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: spawn Update + FixedUpdate threads
L --> M: Started event
M --> C: OnChannelStarted
deactivate M

activate U
loop while IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations()
    U -> L: ProcessConfigChanges / Add / Remove
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E (from pool)
    U -> B: InvokeUpdate(E)  ->  partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: return E to pool
    U -> L: FrameRateControlSync (sleep to 1/TargetFPS)
    U -> L: Interlocked.Increment(ref _totalFrames)
end
deactivate U

activate F
loop while IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval (16 ms)
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    alt E.Handled == false
        F -> L: enqueue E for update-thread drain
    else E.Handled == true
        F -> L: return E to pool
    end
end
deactivate F

C -> M: StopAsync(channel)
activate M
M -> L: cts.Cancel(), join threads, clear queues, reset stats
L --> M: Stopped event
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

Key source: `MonoBehaviourManager.cs` lines 394-441 (`FixedUpdateLoop`), 443-488 (`UpdateLoop`), 610-656 (`ExecuteBehaviorsUpdateSync` / `LateUpdate` / `FixedUpdate`), 245-291 (`Start`), 293-336 (`StopAsync`).

## 2. Pause / Resume / Stop

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update thread" as U

C -> M: Pause(channel)
activate M
M -> L: Pause()
L -> L: _isPaused = true
L --> M: Paused event
M --> C: OnChannelPaused
deactivate M

U -> U: loop sees _isPaused -> PrecisionSleep(10 ms), skip frame

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _isPaused = false
L --> M: Resumed event
M --> C: OnChannelResumed
deactivate M

U -> U: next frame continues normally

C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: join update + fixed threads (1 s timeout)
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped event
M --> C: OnChannelStopped
deactivate M
@enduml
```

## 3. `Handled = true` short-circuit

```plantuml
@startuml
!theme plain

participant "Update thread" as U
participant "Behaviour A" as A
participant "Behaviour B" as B
participant "FrameEventArgs" as E

U -> A: InvokeUpdate(E)
activate A
A -> A: run user Update logic
A -> E: E.Handled = true
A --> U: return
deactivate A

U -> U: check E.Handled == true -> break
note over U,B: Behaviour B is skipped this frame phase
U --> B: (no call)

U -> U: LateUpdate phase also sees Handled == true -> break
@enduml
```

Source: `MonoBehaviourManager.cs` lines 611-624 (`ExecuteBehaviorsUpdateSync` checks `if (frameArgs.Handled || token.IsCancellationRequested) break;`). Runtime probe, 2026-08-17: with a `HaltBehavior` that sets `Handled = true` first, a later `BehaviorB.UpdateCount` stayed at `0`.

## 4. Time scale

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "LoopChannel" as L
participant "FrameEventArgs" as E
participant "IMonoBehaviour" as B

C -> L: SetTimeScale(0.5f, channel)
L -> L: enqueue ConfigChangeRequest{ TimeScale = 0.5f }
note over L: applied on next ProcessConfigChanges()

L -> L: CreateFrameEventArgs(deltaTime)
L -> E: DeltaTime = ScaleDuration(rawDelta, 0.5f)
note over E: raw delta is halved; TimeScale <= 0 yields TimeSpan.Zero
L --> B: InvokeUpdate(E)
B -> B: reads e.DeltaTime (halved) -> slower simulation
@enduml
```

Source: `MonoBehaviourManager.cs` lines 202-210 (`SetTimeScale`), 744-754 (`CreateFrameEventArgs`), 861-867 (`ScaleDuration`). Runtime probe, 2026-08-17: `SetTimeScale(0.5f)` produced a delta-time ratio of ≈ `0.49` vs the unscaled base.
