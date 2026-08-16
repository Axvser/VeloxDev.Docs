# Design Patterns — MVVM

```mermaid
classDiagram
    class VeloxPropertyAttribute {
        <<attribute>>
        +AttributeTargets Field | Property
    }
    class VeloxCommandAttribute {
        <<attribute>>
        +Name string
        +CanValidate bool
        +Semaphore int
    }
    class IVeloxCommand {
        <<interface>>
        <<ICommand>>
        +Created/Started/Completed/Canceled/Failed/Exited/Enqueued/Dequeued events
        +Lock/UnLock/Notify/Clear/Interrupt/Continue/ChangeSemaphore
        +ExecuteAsync(object?) Task
    }
    class VeloxCommand {
        +VeloxCommand(Func, Predicate, int)
        +CreateTaskOnlyWithParameter(...) static
        +CreateTaskOnlyWithCancellationToken(...) static
        -SemaphoreSlim _stateLock
        -Queue~CommandEventArgs~ _pendingQueue
        -List~CommandEventArgs~ _active
        -int _maxConcurrency
        -bool _isForceLocked
    }
    class CommandEventArgs {
        +Parameter object?
        +EventType CommandEventType
        +Exception Exception?
        +Cts CancellationTokenSource?
        +With(newType, ex) CommandEventArgs
    }
    class CommandEventHandler {
        <<delegate>>
        +Invoke(CommandEventArgs) void
    }
    class CommandEventType {
        <<enum>>
        Created Enqueued Dequeued Started Completed Failed Canceled Exited
    }
    class ObservableCollectionTracker {
        <<static>>
        +EnsureSubscribed(collection, handler) void
        +Unsubscribe(collection, handler) void
        -ConditionalWeakTable _table
    }
    class UserVM {
        <<partial>>
        +[VeloxProperty] _index
        +[VeloxCommand] Plus(...)
        +partial OnIndexChanged(...)
        +partial CanExecuteMinusCommand(...)
    }
    class GeneratedVM {
        <<generated>>
        +Index int
        +PlusCommand IVeloxCommand
        +OnIndexChanging/OnIndexChanged partials
        +OnItemsCollectionChanged handler
        +OnItemAddedToItems/... partials
    }

    VeloxCommandAttribute ..> GeneratedVM
    VeloxPropertyAttribute ..> GeneratedVM
    GeneratedVM --> IVeloxCommand
    VeloxCommand ..|> IVeloxCommand
    IVeloxCommand --> CommandEventArgs
    CommandEventHandler --> CommandEventArgs
    GeneratedVM ..> ObservableCollectionTracker
    UserVM --> GeneratedVM
```

## Pattern Map

| # | Pattern | Participants | Where |
|---|---|---|---|
| 1 | Source generation (Template Method / codegen) | `MVVM`, `Command` generators, `MVVMWriter`, `CommandWriter`, `MVVMPropertyFactory` | `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs, Writers/MVVMWriter.cs, Writers/CommandWriter.cs, Base/Analizer.cs}` |
| 2 | Observer (PropertyChanged + lifecycle events) | `VeloxCommand` (9 events), generated properties, `ObservableViewModelBase` | `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`, `Examples/MVVM/WPF/Demo/ObservableViewModelBase.cs` |
| 3 | Command | `IVeloxCommand : ICommand`, `VeloxCommand` (queue + semaphore) | `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` |
| 4 | Template Method (partial hooks) | generated `OnXxxChanging/OnXxxChanged`, collection partials | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`GenerateViewModel`, `GenerateCollectionMembers`) |
| 5 | Weak-reference registry | `ObservableCollectionTracker` with `ConditionalWeakTable` | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` |
| 6 | Adapter (host-framework coexistence) | `MVVMWriter.DetectSetterMode` → `SetProperty` / `RaiseAndSetIfChanged` / `NotifyOfPropertyChange` | `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs` |

## Patterns Identified

### 1. Source Generation / Code Generation (Roslyn incremental generators)

`MVVM` and `Command` implement `IIncrementalGenerator` (`MVVM.cs` lines 12-13; `Command.cs` lines 12-13) and register source output from `partial` class declarations (`Analizer.Filters.FilterContext`). Each writer produces one `.g.cs` file per class. The generated setter shape for the default mode (`Base/Analizer.cs`, `GetSetterBodyLines`, lines 287-307):

```csharp
if(global::System.Object.Equals(_index, value)) return;
var old = _index;
OnPropertyChanging(nameof(Index));
OnIndexChanging(old, value);
_index = value;
OnIndexChanged(old, value);
OnPropertyChanged(nameof(Index));
```

### 2. Observer Pattern (PropertyChanged + command lifecycle events)

`VeloxCommand` exposes eight lifecycle events — `Created`/`Enqueued`/`Dequeued`/`Started`/`Completed`/`Failed`/`Canceled`/`Exited` — plus `CanExecuteChanged` (`VeloxCommand.cs`, lines 92-101). `ExecuteCoreAsync` raises `Started` before invoking, then `Completed`/`Canceled`/`Failed`, then `Exited` (lines 176-204). The generated properties raise `PropertyChanging`/`PropertyChanged` through `OnPropertyChanging`/`OnPropertyChanged`, which the demo base implements as event invocations (`Examples/MVVM/WPF/Demo/ObservableViewModelBase.cs`, lines 11-19).

### 3. Command Pattern (IVeloxCommand)

`IVeloxCommand : ICommand` adds async execution and concurrency control. `ExecuteAsync` checks the force-lock, then either starts immediately (`_active.Count < _maxConcurrency`) or enqueues (`_pendingQueue.Enqueue`) and raises `Enqueued` (`VeloxCommand.cs`, lines 139-174). `TryStartPendingAsync` drains the queue when capacity frees (lines 349-377). `CanExecute` combines the user predicate with the force-lock: `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked` (line 126).

### 4. Template Method Pattern (partial hooks)

The generated code declares `partial void OnXxxChanging/OnXxxChanged` and the collection partials `OnItemAddedToXxx`/`OnItemRemovedFromXxx`/`OnItemMovedInXxx`/`OnItemsResetInXxx`; the user supplies implementations and the generated skeleton calls them at fixed points in the setter / collection handler. The demo fills these in (`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 33-36 and 178-209).

### 5. Weak-Reference Registry (ObservableCollectionTracker)

`ObservableCollectionTracker` keeps `CollectionChanged` subscriptions alive even when the backing field is assigned directly (`= []`). A `ConditionalWeakTable<object, Entry>` keys by collection identity, so the entry is collected with the collection — no leak. The `Entry` dedupes handlers by `(Method, Target)` identity (`MethodTargetEqualityComparer`), making repeated getter accesses idempotent (see the API reference page for the reasoning).

### 6. Adapter / Notification base-class adaptation

Rather than forcing a base class, the generator adapts to whatever notification infrastructure already exists. If the class or a base already declares `OnPropertyChanging`/`OnPropertyChanged` string methods, the generated code calls those instead of generating events (`MVVMWriter.ConfigurePropertyNotificationInfrastructure`, lines 198-258). Framework bases are detected by `DetectSetterMode` (lines 42-89) and their `SetProperty`/`RaiseAndSetIfChanged`/`NotifyOfPropertyChange` is used. This is how the demo reuses its local `ObservableViewModelBase` unchanged.

> Source references: `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs, Writers/MVVMWriter.cs, Writers/CommandWriter.cs, Base/Analizer.cs}`, `Src/Core/VeloxDev.Core/MVVM/{VeloxCommand.cs, ObservableCollectionTracker.cs}`, `Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`, `Examples/MVVM/WPF/Demo/{MainWindowViewModel.cs, ObservableViewModelBase.cs}`.
