# MVVM — `VeloxCommand`

Sealed concrete `IVeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`).

**Primary constructor** (lines 16-18):

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

**Static factories and convenience constructors** (lines 20-77):

| Member | Signature |
|---|---|
| `CreateTaskOnlyWithParameter` | `static VeloxCommand(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — sets `_isCtsNeeded = false` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task>, ...)` | wraps `await command()`; sets `_isCtsNeeded = false` |
| `VeloxCommand(Action<object?>, ...)` | synchronous with parameter; `_isCtsNeeded = false` |
| `VeloxCommand(Action, ...)` | synchronous without parameter; `_isCtsNeeded = false` |

**Exceptions:** `ArgumentNullException` when `command` is `null` (line 79). **Test:** `VeloxCommandTests.Constructor_NullCommand_Throws` (`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`, lines 62-65).

**Internal state** (lines 82-90): `SemaphoreSlim _stateLock(1, 1)`, `Queue<CommandEventArgs> _pendingQueue`, `List<CommandEventArgs> _active`, `int _maxConcurrency = Math.Max(1, semaphore)`, `bool _isForceLocked`, `bool _isCtsNeeded = true`, static `CancellationToken _defct`.

**Behavior:**

- `CanExecute(object?)` — `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked` (line 126).
- `Execute(object?)` — fire-and-forget: `_ = ExecuteAsync(parameter)` (line 128).
- `ExecuteAsync(object?)` — creates a `CommandEventArgs(parameter, Created)` (allocating a `CancellationTokenSource` when `_isCtsNeeded`), raises `Created`, then under `_stateLock` either cancels the item if force-locked (raises `Canceled`), starts it immediately when `_active.Count < _maxConcurrency`, or enqueues it (raises `Enqueued`); finally releases the lock and calls `Notify()` (lines 139-174).
- `ExecuteCoreAsync` — raises `Started`, invokes the command with the item's token (or `_defct`), then raises `Completed` / `Canceled` (on `OperationCanceledException`) / `Failed` (on any other `Exception`, with `CommandEventArgs.Exception`); finally `OnExecutionCompletedAsync` removes the item, raises `Exited`, raises `CanExecuteChanged`, and drains the queue (lines 176-222).
- `LockAsync` / `UnLockAsync` — toggle `_isForceLocked`, notify, and (for `UnLock`) drain the queue (lines 224-253).
- `InterruptAsync` — force-locks, snapshots and clears the active list, cancels each item's CTS and raises `Canceled`, then unlocks (lines 255-279).
- `ClearAsync` — force-locks, snapshots active and dequeues all pending (raising `Dequeued` for each), cancels everything and raises `Canceled`, then unlocks (lines 281-313).
- `ContinueAsync` — if not force-locked, drains the queue (lines 315-329).
- `ChangeSemaphoreAsync` — ignores `< 1`, updates `_maxConcurrency`, drains the queue (lines 331-347).
- `TryStartPendingAsync` — under `_stateLock` moves up to `_maxConcurrency` queued items into `_active` when not force-locked; raises `Dequeued` for each and starts them (lines 349-377).
- `Notify()` — raises `CanExecuteChanged` (line 130). Event raising is exception-safe: `RaiseCommandEvent` swallows subscriber exceptions (lines 114-123).

**Test evidence:** `VeloxCommandTests` — `Execute_SyncAction_Completes`, `Execute_ActionWithParameter_ReceivesParameter`, `Execute_AsyncFunc_Completes`, `CanExecute_NoPredicate_ReturnsTrue`, `CanExecute_WithPredicate_RespectsIt`, `CreateTaskOnlyWithParameter_Works` (`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`, lines 8-82).

**Generated command-property template** (`CommandWriter.cs`, lines 154-186; `canValidate: true` branch, re-indented):

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_MinusCommand = null;
public VeloxDev.MVVM.IVeloxCommand MinusCommand
{
    get
    {
        _buffer_MinusCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Minus,
            canExecute: CanExecuteMinusCommand,
            semaphore: 1);
        return _buffer_MinusCommand;
    }
}
private partial bool CanExecuteMinusCommand(object? parameter);
```

The `canValidate: false` branch uses `canExecute: _ => true` (lines 172-186).
