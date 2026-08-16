# MVVM — `IVeloxCommand`

The runtime contract implemented by `VeloxCommand`.

**Signature** (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`, lines 5-31):

```csharp
public interface IVeloxCommand : ICommand
{
    public event CommandEventHandler? Created;
    public event CommandEventHandler? Started;
    public event CommandEventHandler? Completed;
    public event CommandEventHandler? Canceled;
    public event CommandEventHandler? Failed;
    public event CommandEventHandler? Exited;
    public event CommandEventHandler? Enqueued;
    public event CommandEventHandler? Dequeued;

    public void Lock();
    public void UnLock();
    public void Notify();
    public void Clear();
    public void Interrupt();
    public void Continue();
    public void ChangeSemaphore(int semaphore);

    public Task ExecuteAsync(object? parameter);
    public Task LockAsync();
    public Task UnLockAsync();
    public Task ClearAsync();
    public Task InterruptAsync();
    public Task ContinueAsync();
    public Task ChangeSemaphoreAsync(int semaphore);
}
```

Inherited from `ICommand`: `bool CanExecute(object?)`, `void Execute(object?)`, event `EventHandler CanExecuteChanged`.

**Lifecycle events** — payload is a single `CommandEventArgs`:

| Event | Raised when |
|---|---|
| `Created` | `ExecuteAsync` creates a `CommandEventArgs` for the trigger |
| `Enqueued` | capacity is exhausted and the item joins `_pendingQueue` |
| `Dequeued` | a queued item is moved to the active list |
| `Started` | the command method is about to be invoked |
| `Completed` | the command method returned successfully |
| `Failed` | the command method threw (non-cancellation) |
| `Canceled` | the invocation was canceled (force-lock, `Interrupt`, `Clear`, or `OperationCanceledException`) |
| `Exited` | the invocation finished and was removed from the active list |

**Control methods:**

| Method | Purpose |
|---|---|
| `ExecuteAsync(object?)` | Enqueue/start execution; returns a `Task` that completes once the invocation is dispatched (not when it finishes). |
| `Lock()` / `UnLock()` | Toggle a force-lock; new triggers are canceled while locked, running commands are not interrupted. |
| `Interrupt()` / `InterruptAsync()` | Cancel the currently active invocation(s). |
| `Clear()` / `ClearAsync()` | Cancel active + all queued invocations. |
| `Continue()` / `ContinueAsync()` | Drain the pending queue (e.g. after `UnLock`). |
| `ChangeSemaphore(int)` | Adjust the max-concurrency at runtime (ignored when `< 1`). |
| `Notify()` | Raise `CanExecuteChanged`. |

- **Example:** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 157-180 — `FreeCommand` / `FreeCommandAsync` call `Lock`, `Interrupt`, `Clear`, `UnLock` (and `await`-able twins).
