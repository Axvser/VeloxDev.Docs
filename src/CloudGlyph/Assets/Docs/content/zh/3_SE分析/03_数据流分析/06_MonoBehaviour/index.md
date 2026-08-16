# 数据流 — MonoBehaviour

每个通道由一个 Update 线程与一个 FixedUpdate 线程驱动（`UseAsyncLoop` 为 `true` 时改为两个异步任务）。配置、注册与主线程动作通过并发队列交换，并在每帧开始时排空。

## 1. 通道启动与每帧分发

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update 线程" as U
participant "FixedUpdate 线程" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: 创建 Update + FixedUpdate 线程
L --> M: Started 事件
M --> C: OnChannelStarted
deactivate M

activate U
loop 当 IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations()
    U -> L: ProcessConfigChanges / Add / Remove
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E（来自对象池）
    U -> B: InvokeUpdate(E)  ->  partial void Update(E)
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: 归还 E 到对象池
    U -> L: FrameRateControlSync（睡眠到 1/TargetFPS）
    U -> L: Interlocked.Increment(ref _totalFrames)
end
deactivate U

activate F
loop 当 IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval（16 ms）
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    alt E.Handled == false
        F -> L: 入队 E 供 Update 线程排空
    else E.Handled == true
        F -> L: 归还 E 到对象池
    end
end
deactivate F

C -> M: StopAsync(channel)
activate M
M -> L: cts.Cancel()、汇合线程、清空队列、重置统计
L --> M: Stopped 事件
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

关键源码：`MonoBehaviourManager.cs` 第 394-441 行（`FixedUpdateLoop`）、443-488 行（`UpdateLoop`）、610-656 行（`ExecuteBehaviorsUpdateSync` / `LateUpdate` / `FixedUpdate`）、245-291 行（`Start`）、293-336 行（`StopAsync`）。

## 2. 暂停 / 恢复 / 停止

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update 线程" as U

C -> M: Pause(channel)
activate M
M -> L: Pause()
L -> L: _isPaused = true
L --> M: Paused 事件
M --> C: OnChannelPaused
deactivate M

U -> U: 循环发现 _isPaused -> PrecisionSleep(10 ms)，跳过本帧

C -> M: Resume(channel)
activate M
M -> L: Resume()
L -> L: _isPaused = false
L --> M: Resumed 事件
M --> C: OnChannelResumed
deactivate M

U -> U: 下一帧恢复正常

C -> M: StopAsync(channel)
activate M
M -> L: _isRunning = false; cts.Cancel()
L -> L: 汇合 update + fixed 线程（1 秒超时）
L -> L: ClearQueues(); ResetStatistics()
L --> M: Stopped 事件
M --> C: OnChannelStopped
deactivate M
@enduml
```

## 3. `Handled = true` 短路

```plantuml
@startuml
!theme plain

participant "Update 线程" as U
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
note over U,B: 本帧阶段跳过行为 B
U --> B: （不调用）

U -> U: LateUpdate 阶段同样看到 Handled == true -> break
@enduml
```

出处：`MonoBehaviourManager.cs` 第 611-624 行（`ExecuteBehaviorsUpdateSync` 检查 `if (frameArgs.Handled || token.IsCancellationRequested) break;`）。运行时探针，2026-08-17：当一个 `HaltBehavior` 先把 `Handled` 置 `true`，其后的 `BehaviorB.UpdateCount` 保持为 `0`。

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
note over L: 在下次 ProcessConfigChanges() 时生效

L -> L: CreateFrameEventArgs(deltaTime)
L -> E: DeltaTime = ScaleDuration(rawDelta, 0.5f)
note over E: 原始增量减半；TimeScale <= 0 得 TimeSpan.Zero
L --> B: InvokeUpdate(E)
B -> B: 读取 e.DeltaTime（减半）-> 模拟变慢
@enduml
```

出处：`MonoBehaviourManager.cs` 第 202-210 行（`SetTimeScale`）、744-754 行（`CreateFrameEventArgs`）、861-867 行（`ScaleDuration`）。运行时探针，2026-08-17：`SetTimeScale(0.5f)` 产生的增量时间比值约为 `0.49`（相对未缩放基准）。
