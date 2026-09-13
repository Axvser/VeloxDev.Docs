# 数据流 — MonoBehaviour

每个通道由两个并发的帧驱动驱动：**更新驱动**（注册、配置、`Update` / `LateUpdate`）与**固定驱动**（按固定间隔执行 `FixedUpdate`）。默认情况下它们是两个后台 `Thread`；启用异步循环模式时则以两个 `Task`（`UpdateLoopAsync` / `FixedUpdateLoopAsync`）运行。跨线程通信——注册、移除、配置变更、被转发的动作——都经由并发队列，由更新驱动在每帧开头排空；固定推送的事件参数不经过队列，因为推送一完成它们就直接还回自己的池。

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
    U -> L: _updateSampler.Sample() -> 时间源的位置，已按速率缩放
    U -> L: CreateFrameEventArgs(sample.Delta, sample.Total)
    L --> U: E（来自对象池）
    U -> B: InvokeUpdate(E) -> partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: 归还 E 到池；统计；节奏控制到 1/TargetFPS
end
deactivate U

activate F
loop 当 IsRunning && !cts.Canceled
    F -> L: _fixedSampler.Advance() -> 时间已经支付的步数
    F -> L: CreateFrameEventArgs(step, step 序号 * step)
    L --> F: E（来自同一个池）
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    F -> L: 归还 E 到对象池（Handled 只停止该帧剩下的推送）
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

两个驱动既可以是 `Thread` 也可以是异步 `Task`，取决于循环模式：在使用 `VeloxDev.Core` 的 `net5.0+` 构建的桌面上，`UseAsyncLoop` 默认取 `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()`（桌面上为 false，因此使用名为 `VeloxDev.Update[name]` / `VeloxDev.FixedUpdate[name]`、`Priority = AboveNormal` 的原生线程）；在 `net5.0` 之前的各目标框架上该常量表达式为 `true`；也可用 `SetUseAsyncLoop(bool, channel)` 在 `Start` 前按通道强制指定（通道运行期间调用会抛 `InvalidOperationException`）。异步孪生版本用 `Task.Delay` 取代分块的 `Thread.Sleep`，执行同一套骨架。只有驱动机制不同——队列交换、对象池与事件参数完全共享。

关键源码：`MonoBehaviourManager.cs` 的 `Start`（275-328）、`UpdateLoop`（510-556）、`FixedUpdateLoop`（447-508）、`UpdateLoopAsync`/`FixedUpdateLoopAsync`（558-688）、`StopAsync`（330-375）、`ProcessMainThreadOperations`（754-767）。

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
L -> L: _bus.Pause()
L --> M: Paused 事件
M --> C: OnChannelPaused
deactivate M

U -> U: 泵在时间源的信号上挂起\n（重新走动前零唤醒）

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _bus.Resume()
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

`Pause` / `Resume` 作用于该通道的时间源（锚定到同一时间源的动画也会观测到同样的状态），`Stop` 则翻转 volatile 标志；每个都会立即引发对应的 `LoopChannel` 事件，静态管理器再以带通道名的事件参数把它转发为 `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped`。`RestartAsync`（405-439 行）即 `StopAsync` + 停机确认等待，驱动未及时停止时以 `ForceCleanup()` 兜底，随后等待队列清空再重新 `Start()`。

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

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` 都会在 `frameArgs.Handled` 被置位后立即 break（`MonoBehaviourManager.cs` 第 690-738 行）。由于同一帧里 `Update` 与 `LateUpdate` 两个阶段复用同一个 `FrameEventArgs` 实例，`Update` 期间把 `Handled` 置 `true` 也会在该帧抑制 `LateUpdate`。把 `Handled` 置 `true` 的 `FixedUpdate` 会停止该帧剩下的推送；其参数无论如何都直接还池，中间没有队列。

## 4. 时间缩放

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "LoopChannel" as L
participant "FrameEventArgs" as E
participant "IMonoBehaviour" as B

C -> L: SetTimeScale(0.5f, channel)
L -> L: _bus.SetRate(0.5f)
note over L: 立即生效 —— 时间源自己串行化写入\n（负值被拒绝；速率为 0 冻结时钟）

L -> L: _updateSampler.Sample() 读取时间源的位置
L -> E: DeltaTime = sample.Delta
note over E: 速率由时钟施加，而不是事后作用于增量
L --> B: InvokeUpdate(E)
B -> B: 读取 e.DeltaTime（减半）-> 模拟变慢
@enduml
```

`SetTimeScale` 把速率直接写给该通道的时间源（`Timing/TimeSourceCore.cs` 第 209-231 行），时间源自己串行化写入 —— 所以没有配置队列这一跳，也没有钳制：负值被拒绝而不是被忽略，速率为 `0` 则冻结时钟但不算暂停。速率由时钟本身施加，因此 `CreateFrameEventArgs`（825-836 行）从一个 `TimeSample` 里同时取出 `DeltaTime` 与 `TotalTime`，自己不做任何缩放。FixedUpdate 泵也走同一个方法：它的 `DeltaTime` 是固定步长，速率改变的是每秒到来多少步，而不是一步的大小。

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

关键源码：`ExecuteOnMainThread` 入队（第 241 行，静态包装 1086 行），排空在 `ProcessMainThreadOperations`（754-767 行）内，WPF 跳转见 `MainWindow.xaml.cs`。
