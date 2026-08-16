# 数据流 — MVVM

四张图均追溯自 `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` 的实现与 `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` 中生成的成员。

## （a）命令生命周期：获取信号量 -> Started -> 调用 -> Completed -> 释放 -> Exited

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "IVeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "User method (Plus)" as Method

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(parameter, Created)
Cmd -> Cmd: raise Created
Cmd -> Lock: _stateLock.WaitAsync()  (semaphore acquire)
activate Lock
Cmd -> Cmd: _active.Add(item)   (_active.Count < _maxConcurrency)
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Started
Cmd -> Method: await _command(item.Parameter, item.Cts.Token)
activate Method
Method --> Cmd: return
deactivate Method
Cmd -> Cmd: raise Completed
Cmd -> Lock: _stateLock.WaitAsync()  (release slot)
activate Lock
Cmd -> Cmd: _active.Remove(item)
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Exited
Cmd -> Cmd: RaiseCanExecuteChanged(); TryStartPendingAsync()
Cmd --> UI
deactivate Cmd
@enduml
```

## （b）`semaphore: 1` 下排队：第二次触发 -> Enqueued -> 等待 -> Dequeued

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "IVeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "_pendingQueue" as Queue
participant "User method (first)" as First

UI -> Cmd: first trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
Cmd -> Cmd: _active.Add(first)   (_active.Count == _maxConcurrency == 1)
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Started
Cmd -> First: await _command(...)
activate First

UI -> Cmd: second trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
Cmd -> Queue: _pendingQueue.Enqueue(second)
Cmd -> Cmd: raise Enqueued
Lock --> Cmd
deactivate Lock
Cmd --> UI
deactivate Cmd

First --> Cmd: return
deactivate First
Cmd -> Cmd: raise Completed
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
Cmd -> Cmd: _active.Remove(first)
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Exited
Cmd -> Cmd: TryStartPendingAsync()  (capacity free)
Cmd -> Queue: _pendingQueue.Dequeue()  -> second
Cmd -> Cmd: raise Dequeued
Cmd -> Cmd: _active.Add(second)
Cmd -> Cmd: raise Started
Cmd -> First: await _command(...)  (second body runs)
deactivate Cmd
@enduml
```

## （c）取消路径：InterruptAsync -> Canceled / Failed

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "IVeloxCommand" as Cmd
participant "_active list" as Active
participant "User method (LongRun)" as Method

Caller -> Cmd: InterruptAsync()
activate Cmd
Cmd -> Cmd: LockAsync()   (_isForceLocked = true)
Cmd -> Active: snapshot _active; clear _active
Cmd -> Cmd: item.Cts?.Cancel()  (per active item)
Cmd -> Cmd: raise Canceled  (direct, per item)
Cmd -> Method: token observed cancellation
Method --> Cmd: throw OperationCanceledException
Cmd -> Cmd: catch -> raise Canceled
Cmd -> Cmd: raise Exited  (via OnExecutionCompletedAsync)
Cmd -> Cmd: UnLockAsync()  (_isForceLocked = false; TryStartPendingAsync)
Cmd --> Caller
deactivate Cmd
@enduml
```

错误路径说明（同一源码，第 176-222 行）：

| 路径 | 行为 |
|---|---|
| `InterruptAsync` / `ClearAsync` | 取消条目的 CTS 并为每个受影响的调用触发 `Canceled`；正在运行的方法还可能在观察到 token 后抛出 `OperationCanceledException`，`ExecuteCoreAsync` 同样将其映射为 `Canceled`。 |
| 用户方法抛出异常（非取消） | `ExecuteCoreAsync` 捕获 `Exception ex` 并触发 `Failed`（`CommandEventArgs.Exception`）；`Exited` 仍会在 `finally` 中触发。 |
| 强制锁定时触发 | `ExecuteAsync` 取消新条目并触发 `Canceled`；不开始执行。 |
| `ClearAsync` | 把所有待处理条目出队（每个触发 `Dequeued`），然后对 pending + active 触发 `Canceled`。 |

## （d）`canValidate` 流程：CanExecute 门控

```plantuml
@startuml
!theme plain

participant "Index setter" as Setter
participant "partial OnIndexChanged" as Hook
participant "MinusCommand" as Cmd
participant "WPF binding engine" as WPF

Setter -> Hook: OnIndexChanged(old, new)
Hook -> Cmd: MinusCommand.Notify()
Cmd -> Cmd: RaiseCanExecuteChanged()
Cmd --> WPF: CanExecuteChanged event
WPF -> Cmd: CanExecute(null)
Cmd -> Cmd: (_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked
Note right of Cmd: delegates to CanExecuteMinusCommand -> _index > 0
WPF -> WPF: enable / disable the bound Button
@enduml
```

> 源引用：`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`（`ExecuteAsync`、`ExecuteCoreAsync`、`OnExecutionCompletedAsync`、`TryStartPendingAsync`、`InterruptAsync`、`ClearAsync`）、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`GetSetterBodyLines`、`GenerateCollectionMembers`）、`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。
