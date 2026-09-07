# 数据流 — MVVM

MVVM 功能有两个运行时面，外加一个同时喂养二者的编译期步骤：源码生成器在 `partial` 类上产生可观察属性与懒 `IVeloxCommand` 属性，`VeloxCommand` 则用信号量有界队列与生命周期事件执行带注解的方法。下图追踪生成器输出进入 `INotifyPropertyChanged` 流程的路径，以及 `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` 中命令引擎的各条路径与 `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory`）生成的成员。

`VeloxCommand` 本身与 UI 无关——它用 `SemaphoreSlim` 与队列调度、串行化调用，并在调用上下文上触发事件。当 WPF/Avalonia 的 `Button` 绑定到生成的命令时，框架在 UI 线程调用 `Execute`/`ExecuteAsync`，因此属性变更通知在 UI 线程触发，绑定引擎可以同步更新。

## （a）生成器输出 → INPC 流程

```plantuml
@startuml
!theme plain

participant "Source generator\\nVeloxDev.Generators.MVVM" as Gen
participant "MVVM partial\\nMainWindowViewModel_Demo_MVVM.g.cs" as GVM
participant "Command body\\n(Plus method)" as Body
participant "Binding\\nWPF / Avalonia" as Bind

== compile time: generator output ==
Gen -> GVM: MVVMWriter emits Index property; OnPropertyChanging/\\nOnPropertyChanged methods; OnIndexChanging/OnIndexChanged partial hooks
note right of GVM: merged with the hand-written partial into one type

== runtime: generated setter drives INPC ==
Body -> GVM: Index = newValue
activate GVM
GVM -> GVM: Object.Equals guard (no-op if unchanged)
GVM -> GVM: OnPropertyChanging(nameof(Index))  -> PropertyChanging
GVM -> GVM: OnIndexChanging(old, value)  (user partial hook)
GVM -> GVM: assign backing field
GVM -> GVM: OnIndexChanged(old, value)  (user partial hook)
GVM -> Bind: OnPropertyChanged(nameof(Index)) fires PropertyChanged
Bind -> Bind: re-reads Index, refreshes the bound control
GVM --> Body
deactivate GVM
@enduml
```

## （b）命令执行 → 属性通知

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "PlusCommand\\n(IVeloxCommand)" as Cmd
participant "User method\\nPlus(sender, ct)" as Method
participant "Generated setter\\nIndex / Greeting" as Setter
participant "Binding\\n(Greeting TextBlock)" as Bind

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: CommandEventArgs(Created); raise Created
Cmd -> Cmd: capacity free -> _active.Add + fire ExecuteCoreAsync
Cmd -> Method: await Plus(parameter, ct.Token)
activate Method
Method -> Setter: Index++ ; Greeting = "current index: {Index}"
activate Setter
Setter -> Setter: OnPropertyChanging + assign + OnIndexChanged(old, new)
Setter -> Bind: OnPropertyChanged(nameof(Greeting))
Bind -> Bind: refresh Greeting text
Setter --> Method
deactivate Setter
Method --> Cmd: return
deactivate Method
Cmd -> Cmd: raise Completed; remove from _active
Cmd -> Cmd: raise Exited; RaiseCanExecuteChanged(); TryStartPendingAsync()
Cmd --> UI
deactivate Cmd
@enduml
```

## （c）命令生命周期：获取信号量 -> Started -> 调用 -> Completed -> 释放 -> Exited

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
Cmd -> Cmd: fire ExecuteCoreAsync; _stateLock.Release(); Notify()
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Started
Cmd -> Method: await _command(item.Parameter, item.Cts.Token)
activate Method
Method --> Cmd: return
deactivate Method
Cmd -> Cmd: raise Completed
Cmd -> Lock: _stateLock.WaitAsync()  (remove from _active)
activate Lock
Cmd -> Cmd: _active.Remove(item)
Lock --> Cmd
deactivate Lock
Cmd -> Cmd: raise Exited; RaiseCanExecuteChanged(); TryStartPendingAsync()
Cmd --> UI
deactivate Cmd
@enduml
```

## （d）`semaphore: 1` 下排队：第二次触发 -> Enqueued -> 等待 -> Dequeued

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
Cmd -> Cmd: raise Started; fire ExecuteCoreAsync
Cmd -> First: await _command(...)
activate First

UI -> Cmd: second trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
Cmd -> Queue: _pendingQueue.Enqueue(second)
Cmd -> Cmd: raise Enqueued; release lock; Notify()
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
Cmd -> Cmd: raise Exited; RaiseCanExecuteChanged()
Cmd -> Cmd: TryStartPendingAsync()  (capacity free)
Cmd -> Queue: _pendingQueue.Dequeue()  -> second
Cmd -> Cmd: raise Dequeued; _active.Add(second)
Cmd -> Cmd: raise Started; fire ExecuteCoreAsync (second body runs)
Cmd --> UI
deactivate Cmd
@enduml
```

## （e）取消 / 清空路径

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "IVeloxCommand" as Cmd
participant "_active / _pendingQueue" as Active
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
Cmd -> Cmd: UnLockAsync()  (_isForceLocked = false; Notify(); TryStartPendingAsync)
Cmd --> Caller
deactivate Cmd
@enduml
```

同一源码中的错误路径行为（VeloxCommand.cs 第 139-377 行）：

| 路径 | 行为 |
|---|---|
| `InterruptAsync` / `ClearAsync` | 取消每个受影响调用的 `CancellationTokenSource` 并触发 `Canceled`。观察 token 的运行中方法会抛出 `OperationCanceledException`，`ExecuteCoreAsync` 同样将其映射为 `Canceled`。 |
| 用户方法抛出异常（非取消） | `ExecuteCoreAsync` 捕获 `Exception ex` 并触发 `Failed`（携带 `CommandEventArgs.Exception`）；`Exited` 仍会在 `finally` 中触发。 |
| 强制锁定时触发 | `ExecuteAsync` 取消新条目的 CTS 并触发 `Canceled`；不开始执行。 |
| `ClearAsync` | 把所有待处理条目出队（每个触发 `Dequeued`），然后对 pending + active 触发 `Canceled`。 |

## （f）`canValidate` 门控：属性钩子 -> Notify -> CanExecuteChanged

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

> 源引用：`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`（`ExecuteAsync`、`ExecuteCoreAsync`、`OnExecutionCompletedAsync`、`TryStartPendingAsync`、`InterruptAsync`、`ClearAsync`）、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory.GetSetterBodyLines`、`GenerateCollectionMembers`）、`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。
