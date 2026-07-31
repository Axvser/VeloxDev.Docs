# Data Flow — MVVM

## (a) Setting a `[VeloxProperty]` field

The generated setter (default mode) raises change notifications and forwards to the partial hooks. Setter line source: `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`, `GetSetterBodyLines`, lines 287-307.

```plantuml
@startuml
!theme plain

participant "User code" as User
participant "Generated setter (Index)" as Setter
participant "ObservableViewModelBase" as Base
participant "partial hook (OnIndexChanged)" as Hook
participant "Binding (TextBlock)" as Binding

User -> Setter: Index = 1
activate Setter
Setter -> Setter: Object.Equals(_index, value)? return if equal
Setter -> Base: OnPropertyChanging(nameof(Index))
activate Base
Base --> Setter
deactivate Base
Setter -> Hook: OnIndexChanging(old, new)
Setter -> Setter: _index = value
Setter -> Hook: OnIndexChanged(old, new)
activate Hook
Hook -> Hook: MinusCommand.Notify()
Hook --> Setter
deactivate Hook
Setter -> Base: OnPropertyChanged(nameof(Index))
activate Base
Base -> Binding: PropertyChanged(this, args)
Binding -> Binding: read Index, update TextBlock
Base --> Setter
deactivate Base
Setter --> User
deactivate Setter
@enduml
```

## (b) Executing a `[VeloxCommand]`

Flow through `ExecuteAsync` → semaphore / queue → lifecycle events (VeloxCommand.cs, lines 139-174, 176-204, 206-222).

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "IVeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "_pendingQueue" as Queue
participant "User method (Plus)" as Method

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(Created) + raise Created
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
alt _isForceLocked == true
    Cmd -> Cmd: item.Cts?.Cancel() + raise Canceled
else _active.Count < _maxConcurrency
    Cmd -> Cmd: _active.Add(item)
    Lock --> Cmd
    deactivate Lock
    Cmd -> Cmd: raise Started
    Cmd -> Method: await _command(parameter, ct)
    activate Method
    Method --> Cmd: return / throw
    deactivate Method
    alt success
        Cmd -> Cmd: raise Completed
    else OperationCanceledException
        Cmd -> Cmd: raise Canceled
    else Exception
        Cmd -> Cmd: raise Failed with ex
    end
    Cmd -> Cmd: _active.Remove(item) + raise Exited
    Cmd -> Cmd: RaiseCanExecuteChanged()
    Cmd -> Cmd: TryStartPendingAsync()
else queue (semaphore exhausted)
    Cmd -> Queue: _pendingQueue.Enqueue(item)
    Cmd -> Cmd: raise Enqueued
    Queue --> Cmd
end
Lock --> Cmd
deactivate Lock
Cmd --> UI
deactivate Cmd
@enduml
```

## (c) CanExecute flow with `Notify()`

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

## Error / Concurrency Path Summary

| Scenario | Behavior |
|---|---|
| Force-locked trigger (`Lock()`) | `ExecuteAsync` cancels the new item and raises `Canceled`; no execution starts. |
| Capacity exhausted (`_active.Count == _maxConcurrency`) | The item is enqueued and `Enqueued` raised; `TryStartPendingAsync` later dequeues it (raising `Dequeued`) when capacity frees or after `UnLock` / `Continue` / `ChangeSemaphore`. |
| User method throws | `Failed` is raised with `CommandEventArgs.Exception`; `Exited` still fires. |
| `OperationCanceledException` | `Canceled` is raised. |
| `Interrupt()` | Cancels the active CTS, then `UnLockAsync` re-enables triggers. |
| `Clear()` | Cancels active and dequeues all pending, raising `Dequeued` then `Canceled` for each. |

> Source references: `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` (`ExecuteAsync`, `ExecuteCoreAsync`, `OnExecutionCompletedAsync`, `TryStartPendingAsync`, `InterruptAsync`, `ClearAsync`), `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`GetSetterBodyLines`, `GenerateCollectionMembers`), `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.
