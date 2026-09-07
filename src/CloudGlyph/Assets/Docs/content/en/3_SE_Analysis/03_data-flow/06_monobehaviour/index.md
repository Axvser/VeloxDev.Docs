# Data Flow — MonoBehaviour

Each channel is driven by two concurrent frame drivers: the **update driver** (registration, config, `Update` / `LateUpdate`) and the **fixed driver** (`FixedUpdate` at a fixed interval). By default they are two background `Thread`s; when async-loop mode is enabled they run as two `Task`s (`UpdateLoopAsync` / `FixedUpdateLoopAsync`). All cross-thread communication — registration, removal, config changes, marshalled actions, fixed events — flows through concurrent queues drained by the update driver at the top of each frame.

## 1. Registration → channel start → per-frame tick → stop

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update driver" as U
participant "Fixed driver" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

== Registration (deferred) ==
C -> M: RegisterBehaviour(behaviour, channel)
M -> L: _addQueue.Enqueue(behaviour)
note over L: drained only while the channel runs;\nAwake/Start fire on the drain (update driver)

== Start ==
C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: spawn Update + Fixed drivers (threads or async tasks)
L --> M: Started
M --> C: OnChannelStarted
deactivate M

activate U
loop while IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations()
    note right of U: <= 64 ExecuteOnMainThread actions,\nthen config / add / remove queues
    U -> L: added queue -> InvokeAwake + InvokeStart (once)
    U -> L: DrainFixedUpdateEvents() -> return pooled args
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E (from pool, time-scaled)
    U -> B: InvokeUpdate(E) -> partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: return E to pool; stats; pace to 1/TargetFPS
end
deactivate U

activate F
loop while IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval (default 16 ms)
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E (from same pool)
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    alt E.Handled == false
        F -> L: enqueue E for update-driver drain
    else E.Handled == true
        F -> L: return E to pool
    end
end
deactivate F

== Stop ==
C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: join / await both drivers (1 s timeout)
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

The two drivers can be `Thread`s or async `Task`s depending on the loop mode: on desktop with a `net5.0+` build of `VeloxDev.Core`, `UseAsyncLoop` defaults to `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()` (false on desktop, so native threads named `VeloxDev.Update[name]` / `VeloxDev.FixedUpdate[name]`, `Priority = AboveNormal`); on the pre-`net5.0` targets the constant expression makes it `true`, and it can be forced per channel with `SetUseAsyncLoop(bool, channel)` before `Start` (it throws `InvalidOperationException` while the channel is running). The async twins run the same skeleton with `Task.Delay` in place of `PrecisionSleep`. Only the driver mechanism differs — queue exchange, pools and event args are shared.

Key source: `MonoBehaviourManager.cs` `Start` (246-292), `UpdateLoop` (444-489), `FixedUpdateLoop` (395-442), `UpdateLoopAsync`/`FixedUpdateLoopAsync` (492-605), `StopAsync` (294-337), `ProcessMainThreadOperations` (675-688).

## 2. Pause / Resume / Restart / Stop

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update driver" as U

C -> M: Pause(channel)
activate M
M -> L: Pause()
L -> L: _isPaused = true
L --> M: Paused event
M --> C: OnChannelPaused
deactivate M

U -> U: loop sees _isPaused -> skip frame\n(PrecisionSleep 10 ms; Task.Delay 10 ms in async mode)

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _isPaused = false
L --> M: Resumed event
M --> C: OnChannelResumed
deactivate M

U -> U: next frame resumes normally

C -> M: RestartAsync(channel) (StopAsync -> confirm shutdown -> Start)
note over L: StopAsync waits for both drivers,\nclears queues and resets statistics,\nthen Start() restarts the same channel

C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: join / await update + fixed drivers (1 s timeout)
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped event
M --> C: OnChannelStopped
deactivate M
@enduml
```

`Pause` / `Resume` / `Stop` flip volatile state and raise the matching `LoopChannel` event immediately; the static manager forwards it to `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` with the channel name. `RestartAsync` (353-377) is `StopAsync` followed by a shutdown-confirmation wait, a `ForceCleanup()` fallback when the drivers do not stop in time, a wait for the queues to empty, and a fresh `Start()`.

## 3. `Handled = true` short-circuit

```plantuml
@startuml
!theme plain

participant "Update driver" as U
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
note over U,B: Behaviour B is skipped in this phase
U --> B: (no call)

U -> U: LateUpdate phase re-checks Handled -> break
note over U,B: same pooled E is reused, so LateUpdate is skipped too
@enduml
```

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` all break as soon as `frameArgs.Handled` is set (`MonoBehaviourManager.cs` lines 611-657). Because the same `FrameEventArgs` instance flows through the `Update` then `LateUpdate` phases of a frame, a `Handled = true` set during `Update` also suppresses `LateUpdate` that frame. A `FixedUpdate` that sets `Handled = true` returns its (pooled) args immediately instead of enqueuing them for drain.

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
note over L: applied on the next ProcessConfigChanges()\n(clamped to 0..10)

L -> L: CreateFrameEventArgs(deltaTime) reads _timeScaleBits
L -> E: DeltaTime = ScaleDuration(rawDelta, 0.5f)
note over E: raw delta is halved; scale <= 0 yields TimeSpan.Zero
L --> B: InvokeUpdate(E)
B -> B: reads e.DeltaTime (halved) -> slower simulation
@enduml
```

`SetTimeScale` enqueues a pooled `ConfigChangeRequest`; the update driver applies it (`ProcessConfigChanges`, lines 690-709) and clamps to `0..10`. Because `CreateFrameEventArgs` (745-755) is shared by both drivers, the scale affects `Update`, `LateUpdate` **and** `FixedUpdate` delta times equally; `ScaleDuration` (862-868) returns `TimeSpan.Zero` for `scale <= 0`.

## 5. Marshalling onto the update driver — `ExecuteOnMainThread` and UI hops

```plantuml
@startuml
!theme plain

participant "Any thread" as W
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update driver" as U

W -> M: ExecuteOnMainThread(action, channel)
M -> L: _mainThreadQueue.Enqueue(action)
U -> L: ProcessMainThreadOperations() (top of next frame)
L -> U: dequeue -> action()  (<= 64 per frame, isolated try/catch)
@enduml
```

`ExecuteOnMainThread` marshals a delegate from any thread (a `FixedUpdate`, an external event handler, a worker callback) onto the channel's **update driver** — the timeline's "main" thread — so it is serialized with `Update`/`LateUpdate` and can safely touch state those hooks share. It does **not** post to the OS/UI thread: the update driver is a background loop. In the WPF demo the behaviours run off the UI thread, so pushing results to the window is done with `Dispatcher.Invoke` from inside the hooks (`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs`, `UpdatePerformanceDisplay`/`UpdateComponentStatistics`, lines 143-190).

```plantuml
@startuml
!theme plain

participant "Update driver" as U
participant "Window behaviour" as B
participant "WPF Dispatcher" as D
participant "UI thread" as UI

U -> B: InvokeUpdate(E)
B -> D: Dispatcher.Invoke(() => set TextBlock.Text)
D -> UI: update on the real UI thread
UI --> B: return
@enduml
```

Key source: `ExecuteOnMainThread` enqueue (line 212, static wrapper 1049-1050), drain inside `ProcessMainThreadOperations` (675-688), WPF hop in `MainWindow.xaml.cs`.
