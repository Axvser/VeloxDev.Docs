# 数据流 — MonoBehaviour

每个通道由两个并发的帧驱动驱动：**更新驱动**（注册、配置、`Update` / `LateUpdate`）与**固定驱动**（按固定间隔执行 `FixedUpdate`）。默认情况下它们是两个后台 `Thread`；启用异步循环模式时则以两个 `Task`（`UpdateLoopAsync` / `FixedUpdateLoopAsync`）运行。所有跨线程通信——注册、移除、配置变更、被转发的动作、固定事件——都经由并发队列，由更新驱动在每帧开头排空。

## 1. 注册 → 通道启动 → 每帧 tick → 停止

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "更新驱动" as U
participant "固定驱动" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

== 注册（延迟处理） ==
C -> M: RegisterBehaviour(behaviour, channel)
M -> L: _addQueue.Enqueue(behaviour)
note over L: 仅在通道运行时排空；\nAwake/Start 在排空时触发（更新驱动）

== 启动 ==
C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: 创建 Update + Fixed 驱动（线程或异步任务）
L --> M: Started
M --> C: OnChannelStarted
deactivate M

activate U
loop 当 IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations()
    note right of U: 每帧 <= 64 个 ExecuteOnMainThread 动作，\n然后是 config / add / remove 队列
    U -> L: added 队列 -> InvokeAwake + InvokeStart（各一次）
    U -> L: DrainFixedUpdateEvents() -> 归还池化参数
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E（来自对象池，已做时间缩放）
    U -> B: InvokeUpdate(E) -> partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: 归还 E 到池；统计；节奏控制到 1/TargetFPS
end
deactivate U

activate F
loop 当 IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval（默认 16 ms）
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E（来自同一个池）
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    alt E.Handled == false
        F -> L: 入队 E 供更新驱动排空
    else E.Handled == true
        F -> L: 归还 E 到对象池
    end
end
deactivate F

== 停止 ==
C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: join / await 两个驱动（1 秒超时）
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

两个驱动既可以是 `Thread` 也可以是异步 `Task`，取决于循环模式：在使用 `VeloxDev.Core` 的 `net5.0+` 构建的桌面上，`UseAsyncLoop` 默认取 `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()`（桌面上为 false，因此使用名为 `VeloxDev.Update[name]` / `VeloxDev.FixedUpdate[name]`、`Priority = AboveNormal` 的原生线程）；在 `net5.0` 之前的各目标框架上该常量表达式为 `true`；也可用 `SetUseAsyncLoop(bool, channel)` 在 `Start` 前按通道强制指定（通道运行期间调用会抛 `InvalidOperationException`）。异步孪生版本用 `Task.Delay` 取代 `PrecisionSleep`，执行同一套骨架。只有驱动机制不同——队列交换、对象池与事件参数完全共享。

关键源码：`MonoBehaviourManager.cs` 的 `Start`（246-292）、`UpdateLoop`（444-489）、`FixedUpdateLoop`（395-442）、`UpdateLoopAsync`/`FixedUpdateLoopAsync`（492-605）、`StopAsync`（294-337）、`ProcessMainThreadOperations`（675-688）。

## 2. 暂停 / 恢复 / 重启 / 停止

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "更新驱动" as U

C -> M: Pause(channel)
activate M
M -> L: Pause()
L -> L: _isPaused = true
L --> M: Paused 事件
M --> C: OnChannelPaused
deactivate M

U -> U: 循环发现 _isPaused -> 跳过本帧\n（PrecisionSleep 10 ms；异步模式为 Task.Delay 10 ms）

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _isPaused = false
L --> M: Resumed 事件
M --> C: OnChannelResumed
deactivate M

U -> U: 下一帧恢复正常

C -> M: RestartAsync(channel)（StopAsync -> 确认停机 -> Start）
note over L: StopAsync 等待两个驱动、\n清空队列并重置统计，\n然后 Start() 重启同一通道

C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: join / await update + fixed 驱动（1 秒超时）
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped 事件
M --> C: OnChannelStopped
deactivate M
@enduml
```

`Pause` / `Resume` / `Stop` 直接翻转 volatile 状态并立即引发对应的 `LoopChannel` 事件；静态管理器把它以带通道名的事件参数转发为 `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped`。`RestartAsync`（353-377 行）即 `StopAsync` + 停机确认等待，驱动未及时停止时以 `ForceCleanup()` 兜底，随后等待队列清空再重新 `Start()`。

## 3. `Handled = true` 短路

```plantuml
@startuml
!theme plain

participant "更新驱动" as U
participant "行为 A" as A
participant "行为 B" as B
participant "FrameEventArgs" as E

U -> A: InvokeUpdate(E)
activate A
A -> A: 执行用户 Update 逻辑
A -> E: E.Handled = true
A --> U: 返回
deactivate A

U -> U: 检查 E.Handled == true -> break
note over U,B: 本阶段跳过行为 B
U --> B: （不调用）

U -> U: LateUpdate 阶段重新检查 Handled -> break
note over U,B: 复用的是同一个池化 E，因此 LateUpdate 也被跳过
@enduml
```

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` 都会在 `frameArgs.Handled` 被置位后立即 break（`MonoBehaviourManager.cs` 第 611-657 行）。由于同一帧里 `Update` 与 `LateUpdate` 两个阶段复用同一个 `FrameEventArgs` 实例，`Update` 期间把 `Handled` 置 `true` 也会在该帧抑制 `LateUpdate`。把 `Handled` 置 `true` 的 `FixedUpdate` 会立即归还其（池化的）参数，而不入队等待排空。

## 4. 时间缩放

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "LoopChannel" as L
participant "FrameEventArgs" as E
participant "IMonoBehaviour" as B

C -> L: SetTimeScale(0.5f, channel)
L -> L: 入队 ConfigChangeRequest{ TimeScale = 0.5f }
note over L: 在下次 ProcessConfigChanges() 生效\n（被钳制到 0..10）

L -> L: CreateFrameEventArgs(deltaTime) 读取 _timeScaleBits
L -> E: DeltaTime = ScaleDuration(rawDelta, 0.5f)
note over E: 原始增量减半；scale <= 0 得 TimeSpan.Zero
L --> B: InvokeUpdate(E)
B -> B: 读取 e.DeltaTime（减半）-> 模拟变慢
@enduml
```

`SetTimeScale` 入队一个池化的 `ConfigChangeRequest`；更新驱动应用它（`ProcessConfigChanges`，第 690-709 行）并钳制到 `0..10`。由于 `CreateFrameEventArgs`（745-755 行）被两个驱动共享，时间缩放同样作用于 `Update`、`LateUpdate` **以及** `FixedUpdate` 的增量时间；`ScaleDuration`（862-868 行）对 `scale <= 0` 返回 `TimeSpan.Zero`。

## 5. 转发到更新驱动 — `ExecuteOnMainThread` 与 UI 跳转

```plantuml
@startuml
!theme plain

participant "任意线程" as W
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "更新驱动" as U

W -> M: ExecuteOnMainThread(action, channel)
M -> L: _mainThreadQueue.Enqueue(action)
U -> L: ProcessMainThreadOperations()（下一帧开头）
L -> U: 出队 -> action()（每帧 <= 64 个，各自 try/catch 隔离）
@enduml
```

`ExecuteOnMainThread` 把委托从任意线程（某次 `FixedUpdate`、外部事件处理器、worker 回调）转发到通道的**更新驱动**——即时间线的“主”线程——从而与 `Update`/`LateUpdate` 串行化，可安全触碰这些钩子共享的状态。它**不会**投递到 OS/UI 线程：更新驱动是后台循环。在 WPF 示例中，行为在 UI 线程之外运行，把结果推到窗口是用钩子内部的 `Dispatcher.Invoke` 完成的（`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs` 的 `UpdatePerformanceDisplay`/`UpdateComponentStatistics`，第 143-190 行）。

```plantuml
@startuml
!theme plain

participant "更新驱动" as U
participant "窗口行为" as B
participant "WPF Dispatcher" as D
participant "UI 线程" as UI

U -> B: InvokeUpdate(E)
B -> D: Dispatcher.Invoke(() => 设置 TextBlock.Text)
D -> UI: 在真正的 UI 线程上更新
UI --> B: 返回
@enduml
```

关键源码：`ExecuteOnMainThread` 入队（第 212 行，静态包装 1049-1050 行），排空在 `ProcessMainThreadOperations`（675-688 行）内，WPF 跳转见 `MainWindow.xaml.cs`。
