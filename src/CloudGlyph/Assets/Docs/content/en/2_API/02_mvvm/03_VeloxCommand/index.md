# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the sealed concrete implementation of `IVeloxCommand` (see [IVeloxCommand](../02_IVeloxCommand/index.md)).

**Primary constructor**

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

**Convenience constructors and static factories**

| Member | Signature |
|---|---|
| `VeloxCommand` | `(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — wraps `await command()`; no per-execution cancellation token. |
| `VeloxCommand` | `(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — synchronous, parameterized. |
| `VeloxCommand` | `(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)` — synchronous, parameterless. |
| `CreateTaskOnlyWithParameter` | `static VeloxCommand(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — awaits `command(parameter)`; no per-execution cancellation token. |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — awaits `command(ct)`; a token is created per execution. |

**Exception:** `ArgumentNullException` with parameter name `command` when the primary-constructor `command` delegate is `null` (`_command = command ?? throw new ArgumentNullException(nameof(command));`). Test: `VeloxCommandTests.Constructor_NullCommand_Throws` (`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`).

**Cancellation note:** only the primary constructor and `CreateTaskOnlyWithCancellationToken` create a per-execution `CancellationTokenSource` (`_isCtsNeeded = true`). The other entry points run with the framework's default (never-canceled) token, so the underlying method is not interruptible by `Lock`/`Interrupt`/`Clear`, although the terminal `Canceled` event is still raised for those invocations.

## Members

All `IVeloxCommand` events are implemented: `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`, plus `ICommand.CanExecuteChanged`. Methods:

| Method | Behavior |
|---|---|
| `bool CanExecute(object? parameter)` | `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked`. |
| `void Execute(object? parameter)` | Fire-and-forget dispatch: `_ = ExecuteAsync(parameter);`. |
| `Task ExecuteAsync(object? parameter)` | Allocate a `CommandEventArgs(parameter, Created)` (plus a CTS when cancellable), raise `Created`, then run immediately when below the concurrency cap (raise `Started` → terminal event → `Exited`), or enqueue (raise `Enqueued`; later `Dequeued` on dispatch). Returns when the item is dispatched, not when it finishes. |
| `void Notify()` | Raise `CanExecuteChanged` (subscriber exceptions are swallowed). |
| `void Lock()` / `Task LockAsync()` | Set the force-lock; further triggers are canceled, running invocations continue. |
| `void UnLock()` / `Task UnLockAsync()` | Clear the force-lock and drain the pending queue. |
| `void Interrupt()` / `Task InterruptAsync()` | Force-lock, snapshot and clear the active list, cancel each active item (raising `Canceled`), then unlock. |
| `void Clear()` / `Task ClearAsync()` | Force-lock, snapshot the active list and dequeue all pending (raising `Dequeued` per item), cancel all (raising `Canceled`), then unlock. |
| `void Continue()` / `Task ContinueAsync()` | Drain the pending queue unless force-locked. |
| `void ChangeSemaphore(int)` / `Task ChangeSemaphoreAsync(int)` | Update `_maxConcurrency` (values `< 1` are ignored) and drain. |

Execution is internally synchronized with a `SemaphoreSlim`; events (`RaiseCommandEvent`) and `CanExecuteChanged` raising are exception-safe.

## Usage from generated code

The Command generator emits a lazily-initialized property that calls these constructors/factories. `canValidate: true` form (`CommandWriter.cs` template, applied to `Minus` in `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`):

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

Direct construction is covered by `Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs` (`Execute_SyncAction_Completes`, `Execute_ActionWithParameter_ReceivesParameter`, `Execute_AsyncFunc_Completes`, `CanExecute_NoPredicate_ReturnsTrue`, `CanExecute_WithPredicate_RespectsIt`, `Constructor_NullCommand_Throws`, `CreateTaskOnlyWithParameter_Works`).
