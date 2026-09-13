# Data Flow — MonoBehaviour

Each channel is driven by two concurrent frame pumps: the **update driver** (registration, config, `Update` / `LateUpdate`) and the **fixed driver** (`FixedUpdate` at a fixed interval). By default they are two background `Thread`s; when async-loop mode is enabled they run as two `Task`s (`UpdateLoopAsync` / `FixedUpdateLoopAsync`). Cross-thread communication — registration, removal, config changes, marshalled actions — flows through concurrent queues drained by the update driver at the top of each frame; a fixed push's event args do not, because they are returned to their own pool as soon as the push is done.

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
    U -> L: _updateSampler.Sample() -> the source's position, already rate-scaled
    U -> L: CreateFrameEventArgs(sample.Delta, sample.Total)
    L --> U: E (from pool)
    U -> B: InvokeUpdate(E) -> partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: return E to pool; stats; pace to 1/TargetFPS
end
deactivate U

activate F
loop while IsRunning && !cts.Canceled
    F -> L: _fixedSampler.Advance() -> the steps time has paid for
    F -> L: CreateFrameEventArgs(step, step index * step)
    L --> F: E (from same pool)
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    F -> L: return E to pool (Handled only stops the rest of this frame's pushes)
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

The two drivers can be `Thread`s or async `Task`s depending on the loop mode: on desktop with a `net5.0+` build of `VeloxDev.Core`, `UseAsyncLoop` defaults to `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()` (false on desktop, so native threads named `VeloxDev.Update[name]` / `VeloxDev.FixedUpdate[name]`, `Priority = AboveNormal`); on the pre-`net5.0` targets the constant expression makes it `true`, and it can be forced per channel with `SetUseAsyncLoop(bool, channel)` before `Start` (it throws `InvalidOperationException` while the channel is running). The async twins run the same skeleton with `Task.Delay` in place of the chunked `Thread.Sleep`. Only the driver mechanism differs — queue exchange, pools and event args are shared.

Key source: `MonoBehaviourManager.cs` `Start` (275-328), `UpdateLoop` (510-556), `FixedUpdateLoop` (447-508), `UpdateLoopAsync`/`FixedUpdateLoopAsync` (558-688), `StopAsync` (330-375), `ProcessMainThreadOperations` (754-767).

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
L -> L: _bus.Pause()
L --> M: Paused event
M --> C: OnChannelPaused
deactivate M

U -> U: the pump parks on the source's signal\n(zero wake-ups until it moves again)

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _bus.Resume()
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

`Pause` / `Resume` act on the channel's time source, which is also what an animation anchored to that source observes; `Stop` flips a volatile flag. Each raises the matching `LoopChannel` event immediately, and the static manager forwards it to `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` with the channel name. `RestartAsync` (405-439) is `StopAsync` followed by a shutdown-confirmation wait, a `ForceCleanup()` fallback when the drivers do not stop in time, a wait for the queues to empty, and a fresh `Start()`.

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

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` all break as soon as `frameArgs.Handled` is set (`MonoBehaviourManager.cs` lines 690-738). Because the same `FrameEventArgs` instance flows through the `Update` then `LateUpdate` phases of a frame, a `Handled = true` set during `Update` also suppresses `LateUpdate` that frame. A `FixedUpdate` that sets `Handled = true` stops the rest of that frame's pushes; its args return to the pool either way, with no queue in between.

## 4. Time scale

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "LoopChannel" as L
participant "FrameEventArgs" as E
participant "IMonoBehaviour" as B

C -> L: SetTimeScale(0.5f, channel)
L -> L: _bus.SetRate(0.5f)
note over L: applied inline — the source serialises its own writers\n(negative is rejected; a rate of 0 freezes the clock)

L -> L: _updateSampler.Sample() reads the transport's position
L -> E: DeltaTime = sample.Delta
note over E: the rate was applied by the clock, not to the delta afterwards
L --> B: InvokeUpdate(E)
B -> B: reads e.DeltaTime (halved) -> slower simulation
@enduml
```

`SetTimeScale` writes the rate straight to the channel's time source (`Timing/TimeSourceCore.cs` lines 209-231), which serialises its own writers — so there is no config hop, and no clamping: a negative rate is rejected rather than ignored, and a rate of `0` freezes the clock without pausing it. The rate is applied by the clock itself, so `CreateFrameEventArgs` (lines 825-836) hands `DeltaTime` and `TotalTime` out of one `TimeSample` and does no scaling of its own. The fixed pump draws from the same method: its `DeltaTime` is the fixed step, and the rate changes how many steps arrive per second rather than the size of a step.

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

Key source: `ExecuteOnMainThread` enqueue (line 241, static wrapper 1086), drain inside `ProcessMainThreadOperations` (754-767), WPF hop in `MainWindow.xaml.cs`.
