# MVVM — `IVeloxCommand`

`VeloxDev.MVVM.IVeloxCommand` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`) is the command contract. It extends `System.Windows.Input.ICommand` with an async execution model, a per-execution lifecycle, and runtime lock / interrupt / queue controls. The concrete implementation is `VeloxCommand` (see [03_VeloxCommand](../03_VeloxCommand/index.md)).

**Signature**

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

**Inherited from `ICommand`:** `bool CanExecute(object? parameter)`, `void Execute(object? parameter)`, event `EventHandler? CanExecuteChanged`.

## Lifecycle events

Every lifecycle event carries a single `CommandEventArgs` (see [06_CommandEventArgs](../06_CommandEventArgs/index.md)) describing one execution. In the normal flow a `Created` invocation runs immediately (`Started`) or waits in the queue (`Enqueued`), then — through `Dequeued` → `Started` — reaches a terminal state (`Completed`, `Failed` or `Canceled`), and `Exited` closes the lifecycle. An invocation canceled before it ever started (while force-locked, or still queued when `Clear` runs) raises `Canceled` directly, without `Started` / `Exited`.

| Event | Raised when |
|---|---|
| `Created` | `ExecuteAsync` allocates the payload for the trigger |
| `Enqueued` | capacity is exhausted and the item joins the pending queue |
| `Dequeued` | a queued item is moved to the active list |
| `Started` | the command method is about to be invoked |
| `Completed` | the command method returned successfully |
| `Failed` | the command method threw a non-cancellation exception |
| `Canceled` | the invocation was canceled (force-lock, `Interrupt`, `Clear`, or `OperationCanceledException`) |
| `Exited` | the invocation finished and was removed from the active list |

## Control methods

| Method | Purpose |
|---|---|
| `ExecuteAsync(object?)` | Dispatch one execution: run immediately when below the concurrency cap, otherwise enqueue. The returned `Task` completes once the item is dispatched, not when the command method finishes. |
| `Lock()` / `LockAsync()` | Enter the force-locked state: new triggers are canceled, running commands keep running. |
| `UnLock()` / `UnLockAsync()` | Leave the force-locked state and drain the pending queue. |
| `Interrupt()` / `InterruptAsync()` | Cancel the active invocation(s). |
| `Clear()` / `ClearAsync()` | Cancel the active invocation(s) and all queued ones. |
| `Continue()` / `ContinueAsync()` | Drain the pending queue (no-op while force-locked). |
| `ChangeSemaphore(int)` / `ChangeSemaphoreAsync(int)` | Adjust the max-concurrency cap at runtime (`< 1` is ignored). |
| `Notify()` | Raise `CanExecuteChanged`. |

The sync control methods are fire-and-forget conveniences; the `Async` variants are the real work and are `await`-able. When a predicate is registered (see `canValidate` in [01_VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md)), call `Notify()` after state changes that affect `CanExecute`.

**Example** (`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 158-179): `FreeCommand` / `FreeCommandAsync` exercise `Lock`, `Interrupt`, `Clear`, `UnLock` and their `await`-able twins against `MinusCommand`.
