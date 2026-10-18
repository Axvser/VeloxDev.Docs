# 数据流 — 命令生命周期

执行管线位于 `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs`。设计所依赖的不变量在源码中写明：`_stateLock` 是 `SemaphoreSlim(1,1)`，因此**不可重入** —— 持锁期间不得运行任何用户代码（事件处理器、命令体都不行）。每个事件都在 `Release()` 之后触发。

## (a) 立即运行：Created → Started → Completed → Exited

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "CommandPipeline" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "命令体\nIncrement(parameter, ct)" as Body
participant "订阅者" as Sub

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(parameter, Created)
Cmd -> Cmd: _isCtsNeeded 为真时挂上 CancellationTokenSource
Cmd -> Sub: 触发 Created
Cmd -> Lock: WaitAsync()
activate Lock
Cmd -> Cmd: _active.Count < _maxConcurrency -> _active.Add(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Cmd: 启动 ExecuteCoreAsync(item)；Notify()
Cmd -> Sub: 触发 Started
Cmd -> Body: await _command(item.Parameter, item.Cts.Token)
activate Body
Body -> Body: Index++ ; Greeting = "current index: {Index}"
Body --> Cmd: 返回（或抛出）
deactivate Body
alt 方法体正常返回
    Cmd -> Sub: 触发 Completed
else 方法体抛出 OperationCanceledException
    Cmd -> Sub: 触发 Canceled（先到者胜）
else 方法体抛出其它异常
    Cmd -> Sub: 触发 Failed，携带 e.Exception
end
Cmd -> Lock: WaitAsync()（finally：_active.Remove(item)）
activate Lock
Cmd -> Cmd: _active.Remove(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Sub: 触发 Exited
Cmd -> Cmd: TryStartPendingAsync(); RaiseCanExecuteChanged()
Cmd --> UI
deactivate Cmd
@enduml
```

> 源码：`CommandPipeline{TParam,TResult}.cs` —— `ExecuteCore`、`ExecuteCoreAsync`、`OnExecutionCompletedAsync`、`TryStartPendingAsync`。

## (b) 容量已满时排队：Enqueued … Dequeued

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "CommandPipeline" as Cmd
participant "_pendingQueue" as Queue
participant "命令体（第一条）" as First

UI -> Cmd: 第一次触发：Execute(null)
activate Cmd
Cmd -> Cmd: 触发 Created；槽位空闲，_active.Add(first)
Cmd -> First: await _command(item.Parameter, ct)
activate First

UI -> Cmd: 第二次触发：Execute(null)
activate Cmd
Cmd -> Cmd: 触发 Created
Cmd -> Cmd: _active.Count == _maxConcurrency
Cmd -> Queue: Enqueue(second)
Cmd -> Cmd: 触发 Enqueued；Notify()
Cmd --> UI
deactivate Cmd

First --> Cmd: 返回
deactivate First
Cmd -> Cmd: 触发 Completed
Cmd -> Cmd: finally：_active.Remove(first)；触发 Exited
Cmd -> Cmd: TryStartPendingAsync()
Cmd -> Queue: Dequeue() -> second ; _active.Add(second)
Cmd -> Cmd: 触发 Dequeued
Cmd -> Cmd: 启动 ExecuteCoreAsync(second)
Cmd --> UI
deactivate Cmd
@enduml
```

> 源码：`ExecuteCore` 的入队分支；`TryStartPendingAsync`。

## (c) 锁下拒绝：Created → Canceled，别无其它

```plantuml
@startuml
!theme plain

participant "调用方" as Caller
participant "CommandPipeline" as Cmd
participant "命令体" as Body
participant "等待 sink（若有）" as Sink

Caller -> Cmd: _isForceLocked 时 ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: 触发 Created
Cmd -> Cmd: 锁内：forceLocked == true -> 既不启动也不入队
Cmd -> Cmd: item.Cts?.Cancel()
Cmd -> Cmd: 触发 Canceled
Cmd -> Cmd: item.TakeCts()?.Dispose()
Cmd -> Sink: Complete(CommandOutcome.Refused, null)
note right of Body: 从未进入 - 没有 Started，没有 Exited
Cmd --> Caller
deactivate Cmd
@enduml
```

> 源码：`ExecuteCore` 的 `forceLocked` 分支。这是产生 `CommandOutcome.Refused` 的唯一路径，也是 `CommandEventType` 无法表达拒绝的原因。

## (d) 取消与清空

```plantuml
@startuml
!theme plain

participant "调用方" as Caller
participant "CommandPipeline" as Cmd
participant "_active / _pendingQueue" as Sets
participant "命令体（运行中）" as Body

Caller -> Cmd: InterruptAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync() —— 记住此前是否已锁定
Cmd -> Sets: 快照 _active ; _active.Clear()
Cmd -> Body: it.Cts?.Cancel()
activate Body
Body --> Cmd: 抛出 OperationCanceledException
deactivate Body
Cmd -> Cmd: 对每个活动项直接触发 Canceled
Cmd -> Body: 方法体自己的 OCE 到达 ExecuteCoreAsync
Cmd -> Cmd: RaiseCanceled -> TryMarkCancelReported 挡掉第二次上报
Cmd -> Cmd: 在 ExecuteCoreAsync 的 finally 中触发 Exited
Cmd -> Cmd: 此前未锁定时 UnlockAsync()
Cmd --> Caller
deactivate Cmd

== Clear 是同样的流程，外加队列 ==

Caller -> Cmd: ClearAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync()
Cmd -> Sets: 快照 _active ; 把 _pendingQueue 排空到 pendingToCancel
Cmd -> Cmd: 按队列顺序为每个排队项触发 Dequeued
Cmd -> Cmd: 每个排队项：Cancel(); 触发 Canceled; TakeCts()?.Dispose(); CompleteTyped(Canceled, null); Complete(Canceled, null)
Cmd -> Cmd: 每个活动项：Cancel(); 触发 Canceled
Cmd -> Cmd: 此前未锁定时 UnlockAsync()
Cmd --> Caller
deactivate Cmd
@enduml
```

> 源码：`InterruptAsync`、`ClearAsync`、`RaiseCanceled`、`TryMarkCancelReported`。

```csharp
// Source: Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs
// 一次执行最多上报一条 Canceled。Interrupt/Clear 会及时上报；
// 方法体随后抛出的 OperationCanceledException 会被 TryMarkCancelReported 挡掉。
private void RaiseCanceled(CommandEventArgs<TParam, TResult> item)
{
    if (item.TryMarkCancelReported())
    {
        RaiseCommandEventAs(Canceled, item, CommandEventType.Canceled);
    }
}
```

## (e) `canValidate` 闸门：属性钩子 → Notify → CanExecuteChanged

```plantuml
@startuml
!theme plain

participant "生成的 setter\nIndex" as Setter
participant "partial OnIndexChanged" as Hook
participant "MinusCommand\n(IVeloxCommand)" as Cmd
participant "WPF / Avalonia 绑定引擎" as Bind

Setter -> Hook: OnIndexChanged(old, new)
Hook -> Cmd: MinusCommand.Notify()
Cmd -> Cmd: RaiseCanExecuteChanged()
alt EventContext 为 null 或已是当前上下文
    Cmd -> Bind: 内联触发 CanExecuteChanged
else EventContext 指向其它上下文
    Cmd -> Cmd: context.Post(...)（异步，按生命周期顺序）
end
Bind -> Cmd: CanExecute(null)
activate Cmd
Cmd -> Cmd: predicate(parameter) && !_isForceLocked
note right of Cmd: 委托给 CanExecuteMinusCommand -> _index > 0
Cmd --> Bind: true / false
deactivate Cmd
Bind -> Bind: 启用 / 禁用绑定的 Button
@enduml
```

> 源码：`CommandPipeline{TParam,TResult}.cs` 中的 `Notify` / `RaiseCanExecuteChanged` / `CanExecute`；钩子位于 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。

## 错误路径汇总

| 路径 | 行为 |
| --- | --- |
| 方法体抛出非取消异常 | `outcome = Failed`，触发带 `CommandEventArgs.Exception` 的 `Failed`；`Exited` 仍会在 `finally` 中触发。 |
| 方法体抛出 `OperationCanceledException` | `outcome = Canceled`，触发 `Canceled` —— 除非 `Interrupt` / `Clear` 已为该执行上报过。 |
| 锁定时触发 | 既不启动也不入队；触发 `Canceled`，并以 `Refused` 完成 sink。 |
| 队列中有调用时执行 `Clear` | 每个排队项先 `Dequeued` 再 `Canceled`；该项永不到达 `Started` / `Exited`。 |
| 取消回调抛异常 | 被吞掉（`AggregateException`），否则逃逸会跳过 `UnlockAsync`，让命令永久锁定。 |
| `Cancel` 时遇到 `ObjectDisposedException` | 被吞掉：方法体可能已经结束并释放了自己的源。 |
| 订阅者抛异常 | 被捕获并通过静态 `HandlerException` 上报；生命周期不受影响。 |
| `OnExecutionCompletedAsync` 抛异常 | 嵌套 `finally` 仍会完成 sink 并释放源。 |
