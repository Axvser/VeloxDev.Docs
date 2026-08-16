# Data Flow — MVVM

All four diagrams trace the implementation in `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` and the generated members in `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`.

## (a) Command lifecycle: semaphore acquire -> Started -> invoke -> Completed -> release -> Exited

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

## (b) Queueing under `semaphore: 1`: second trigger -> Enqueued -> wait -> Dequeued

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

## (c) Cancellation path: InterruptAsync -> Canceled / Failed

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

Notes on the error paths (same source, lines 176-222):

| Path | Behavior |
|---|---|
| `InterruptAsync` / `ClearAsync` | Cancel the item CTS and raise `Canceled` for each affected invocation; the running method may additionally observe the token and throw `OperationCanceledException`, which `ExecuteCoreAsync` also maps to `Canceled`. |
| User method throws (non-cancellation) | `ExecuteCoreAsync` catches `Exception ex` and raises `Failed` with `CommandEventArgs.Exception`; `Exited` still fires in `finally`. |
| Force-locked trigger | `ExecuteAsync` cancels the new item and raises `Canceled`; no execution starts. |
| `ClearAsync` | Dequeues all pending (raising `Dequeued` per item), then raises `Canceled` for pending + active. |

## (d) `canValidate` flow: CanExecute gate

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

> Source references: `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` (`ExecuteAsync`, `ExecuteCoreAsync`, `OnExecutionCompletedAsync`, `TryStartPendingAsync`, `InterruptAsync`, `ClearAsync`), `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`GetSetterBodyLines`, `GenerateCollectionMembers`), `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.
