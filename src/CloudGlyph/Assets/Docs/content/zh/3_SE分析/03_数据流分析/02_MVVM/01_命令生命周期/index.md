# 数据流分析 — 命令生命周期

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` 中的执行管线。整个设计赖以成立的不变式写在源码自身里（`VeloxCommand.cs` 第 192-194 行）：`_stateLock` 是 `SemaphoreSlim(1,1)`，因此**不可重入**，持锁期间不得运行任何用户代码 —— 既不能是事件处理器，也不能是命令方法体。每次 `RaiseCommandEvent` 都发生在 `Release()` 之后。

## (a) 立即运行：Created → Started → Completed → Exited

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "VeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "Command body\nIncrement(parameter, ct)" as Body
participant "Subscribers" as Sub

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(parameter, Created)
Cmd -> Cmd: attach a CancellationTokenSource when _isCtsNeeded
Cmd -> Sub: raise Created
Cmd -> Lock: WaitAsync()
activate Lock
Cmd -> Cmd: _active.Count < _maxConcurrency  ->  _active.Add(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Cmd: fire ExecuteCoreAsync(item); Notify()
Cmd -> Sub: raise Started
Cmd -> Body: await _command(item.Parameter, item.Cts.Token)
activate Body
Body -> Body: Index++ ; Greeting = "current index: {Index}"
Body --> Cmd: return (or throw)
deactivate Body
alt body returned normally
    Cmd -> Sub: raise Completed
else body threw OperationCanceledException
    Cmd -> Sub: raise Canceled (first emitter wins)
else body threw anything else
    Cmd -> Sub: raise Failed with e.Exception
end
Cmd -> Lock: WaitAsync()  (finally: _active.Remove(item))
activate Lock
Cmd -> Cmd: _active.Remove(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Sub: raise Exited
Cmd -> Cmd: TryStartPendingAsync(); RaiseCanExecuteChanged()
Cmd --> UI
deactivate Cmd
@enduml
```

> 来源：`VeloxCommand.cs` —— `ExecuteCore` 第 474-531 行、`ExecuteCoreAsync` 第 533-580 行、`OnExecutionCompletedAsync` 第 582-598 行。

## (b) 容量已满时排队：Enqueued …… Dequeued

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "VeloxCommand" as Cmd
participant "_pendingQueue" as Queue
participant "Command body (first)" as First

UI -> Cmd: first trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created; _active.Add(first) because the slot is free
Cmd -> First: await _command(item.Parameter, ct)
activate First

UI -> Cmd: second trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Cmd: _active.Count == _maxConcurrency
Cmd -> Queue: Enqueue(second)
Cmd -> Cmd: raise Enqueued; Notify()
Cmd --> UI
deactivate Cmd

First --> Cmd: return
deactivate First
Cmd -> Cmd: raise Completed
Cmd -> Cmd: finally: _active.Remove(first); raise Exited
Cmd -> Cmd: TryStartPendingAsync()
Cmd -> Queue: Dequeue() -> second ; _active.Add(second)
Cmd -> Cmd: raise Dequeued
Cmd -> Cmd: fire ExecuteCoreAsync(second)
Cmd --> UI
deactivate Cmd
@enduml
```

> 来源：`VeloxCommand.cs` —— 入队分支第 503-505 与 521-524 行，`TryStartPendingAsync` 第 794-822 行（排空循环在第 801-809 行）。

## (c) 锁定下拒绝：Created → Canceled，别无其它

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "VeloxCommand" as Cmd
participant "Command body" as Body
participant "Awaiting sink (if any)" as Sink

Caller -> Cmd: ExecuteAsync(null) while _isForceLocked
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Cmd: under the lock: forceLocked == true  ->  neither start nor enqueue
Cmd -> Cmd: item.Cts?.Cancel()
Cmd -> Cmd: raise Canceled
Cmd -> Cmd: item.TakeCts()?.Dispose()
Cmd -> Sink: item.Complete(CommandOutcome.Refused, null)
note right of Body: never entered - no Started, no Exited
Cmd --> Caller
deactivate Cmd
@enduml
```

> 来源：`VeloxCommand.cs` 第 513-520 行。这是产生 `CommandOutcome.Refused` 的唯一路径，也是单看 `CommandEventType` 无法表达拒绝的原因（`CommandCompletion.cs` 第 22-28 行）。

## (d) 取消与清空

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "VeloxCommand" as Cmd
participant "_active / _pendingQueue" as Sets
participant "Command body (running)" as Body

Caller -> Cmd: InterruptAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync() - remembers whether it was already locked
Cmd -> Sets: snapshot _active ; _active.Clear()
Cmd -> Body: it.Cts?.Cancel()
activate Body
Body --> Cmd: throws OperationCanceledException
deactivate Body
Cmd -> Cmd: raise Canceled (direct, for each active item)
Cmd -> Body: the body's own OCE reaches ExecuteCoreAsync
Cmd -> Cmd: RaiseCanceled -> TryMarkCancelReported blocks the second report
Cmd -> Cmd: raise Exited from ExecuteCoreAsync's finally
Cmd -> Cmd: if it was not locked before, UnlockAsync()
Cmd --> Caller
deactivate Cmd

== Clear is the same plus the queue ==

Caller -> Cmd: ClearAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync()
Cmd -> Sets: snapshot _active ; drain _pendingQueue into pendingToCancel
Cmd -> Cmd: raise Dequeued for every pending item, in queue order
Cmd -> Cmd: per pending item: Cancel(); raise Canceled; TakeCts()?.Dispose(); Complete(Canceled, null)
Cmd -> Cmd: per active item: Cancel(); raise Canceled
Cmd -> Cmd: UnlockAsync() if it was not locked before
Cmd --> Caller
deactivate Cmd
@enduml
```

> 来源：`VeloxCommand.cs` —— `InterruptAsync` 第 642-683 行、`ClearAsync` 第 686-747 行、`RaiseCanceled` 第 398-404 行、`TryMarkCancelReported` 第 896 行。

```csharp
// Source: Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs, lines 396-404
// One execution reports at most one Canceled. Interrupt/Clear report promptly;
// the body's own OperationCanceledException arrives later and is blocked by TryMarkCancelReported.
private void RaiseCanceled(CommandEventArgs item)
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

participant "Generated setter\nIndex" as Setter
participant "partial OnIndexChanged" as Hook
participant "MinusCommand\n(IVeloxCommand)" as Cmd
participant "WPF / Avalonia binding engine" as Bind

Setter -> Hook: OnIndexChanged(old, new)
Hook -> Cmd: MinusCommand.Notify()
Cmd -> Cmd: RaiseCanExecuteChanged()
alt EventContext is null or already current
    Cmd -> Bind: CanExecuteChanged raised inline
else EventContext is set to another context
    Cmd -> Cmd: context.Post(...)  (asynchronous, in lifecycle order)
end
Bind -> Cmd: CanExecute(null)
activate Cmd
Cmd -> Cmd: (_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked
note right of Cmd: delegates to CanExecuteMinusCommand -> _index > 0
Cmd --> Bind: true / false
deactivate Cmd
Bind -> Bind: enable / disable the bound Button
@enduml
```

> 来源：`VeloxCommand.cs` —— `Notify` 第 414 行、`RaiseCanExecuteChanged` 第 328-339 行、`CanExecute` 第 407-408 行；钩子见 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs` 第 34-38 行。

## 错误路径汇总

| 路径 | 行为 |
|---|---|
| 方法体抛非取消异常 | `outcome = Failed`、`failure = ex`，触发带 `CommandEventArgs.Exception` 的 `Failed`；`Exited` 仍从 `finally` 触发。 |
| 方法体抛 `OperationCanceledException` | `outcome = Canceled`，触发 `Canceled` —— 除非 `Interrupt` / `Clear` 已为该次执行报过一条。 |
| 强制锁定下的触发 | 既不启动也不入队；触发 `Canceled` 并以 `Refused` 收尾 sink。 |
| 有调用在排队时执行 `Clear` | 每个排队项先 `Dequeued` 再 `Canceled`；这样的项永远到不了 `Started` / `Exited`。 |
| 取消回调抛异常 | 被吞掉（`AggregateException`），因为让它逃逸会跳过 `UnlockAsync`，让命令永久锁死（`VeloxCommand.cs` 第 669-673、735-739 行）。 |
| `Cancel` 抛 `ObjectDisposedException` | 被吞掉：方法体可能已经跑完并释放了自己的源（第 665-668 行）。 |
| 订阅者抛异常 | 被捕获并经静态 `HandlerException` 上报；生命周期不受影响。 |
| `OnExecutionCompletedAsync` 抛异常 | 内层 `finally` 仍会执行 `item.Complete(...)` 与 `TakeCts()?.Dispose()`（第 569-578 行）。 |
