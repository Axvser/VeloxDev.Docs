# Data Flow — MVVM

The MVVM feature has two runtime surfaces plus a compile-time step that feeds both: the source generator produces observable properties and lazy `IVeloxCommand` properties on a `partial` class, and `VeloxCommand` executes the annotated methods with a semaphore-bounded queue and lifecycle events. The diagrams below trace the generator output into the `INotifyPropertyChanged` flow and the command engine paths in `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` and the generated members produced by `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory`).

`VeloxCommand` itself is UI-agnostic — it schedules and serializes invocations with a `SemaphoreSlim` and a queue and raises events on the calling context. When a WPF/Avalonia `Button` is bound to a generated command, the framework calls `Execute`/`ExecuteAsync` on the UI thread, so property-change notifications are raised there and the binding engine can update synchronously.

## (a) Generator output → INPC flow

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

## (b) Command execute → property notification

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

## (c) Command lifecycle: acquire -> Started -> invoke -> Completed -> release -> Exited

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

## (d) Queueing under `semaphore: 1`: second trigger -> Enqueued -> wait -> Dequeued

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

## (e) Cancellation / clear paths

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

Error-path behavior from the same source (VeloxCommand.cs lines 139-377):

| Path | Behavior |
|---|---|
| `InterruptAsync` / `ClearAsync` | Cancel each affected invocation's `CancellationTokenSource` and raise `Canceled`. A running method that observes the token throws `OperationCanceledException`, which `ExecuteCoreAsync` also maps to `Canceled`. |
| User method throws (non-cancellation) | `ExecuteCoreAsync` catches `Exception ex` and raises `Failed` with `CommandEventArgs.Exception`; `Exited` still fires in `finally`. |
| Force-locked trigger | `ExecuteAsync` cancels the new item's CTS and raises `Canceled`; no execution starts. |
| `ClearAsync` | Dequeues all pending items (raising `Dequeued` per item), then raises `Canceled` for pending + active. |

## (f) `canValidate` gate: property hook -> Notify -> CanExecuteChanged

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

> Source references: `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` (`ExecuteAsync`, `ExecuteCoreAsync`, `OnExecutionCompletedAsync`, `TryStartPendingAsync`, `InterruptAsync`, `ClearAsync`), `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory.GetSetterBodyLines`, `GenerateCollectionMembers`), `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.
