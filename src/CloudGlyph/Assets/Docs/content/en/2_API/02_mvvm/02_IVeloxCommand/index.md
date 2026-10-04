# MVVM — `IVeloxCommand`

`VeloxDev.MVVM.IVeloxCommand` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`) is the command contract. It extends `System.Windows.Input.ICommand` with an async execution model, a per-execution lifecycle, and runtime lock / interrupt / queue controls. The concrete implementation is `VeloxCommand` (see `05_VeloxCommand`).

## Interface: `IVeloxCommand`

**Signature**

```csharp
using System.Windows.Input;

namespace VeloxDev.MVVM
{
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
        public void Unlock();
        public void Notify();
        public void Clear();
        public void Interrupt();
        public void Continue();
        public void ChangeSemaphore(int semaphore);

        public Task ExecuteAsync(object? parameter);
        public Task LockAsync();
        public Task UnlockAsync();
        public Task ClearAsync();
        public Task InterruptAsync();
        public Task ContinueAsync();
        public Task ChangeSemaphoreAsync(int semaphore);
    }
}
```

**Inherited from `ICommand`:** `bool CanExecute(object? parameter)`, `void Execute(object? parameter)`, event `EventHandler? CanExecuteChanged`.

**Not declared here:** `ExecuteAndWaitAsync` (on `IVeloxCommandCompletion`), `IsBusy` / `ActiveCount` / `PendingCount` (on `IVeloxCommandStatus`). Both are reachable from this interface through `VeloxCommandExtensions` — adding them to `IVeloxCommand` would break every hand-written implementer.

##### Events

| Name | Type | Description |
|---|---|---|
| `Created` | `CommandEventHandler?` | Raised when an execution request has been accepted. |
| `Enqueued` | `CommandEventHandler?` | Raised when capacity is exhausted and the request joins the pending queue. |
| `Dequeued` | `CommandEventHandler?` | Raised when a queued item leaves the queue and is about to run. |
| `Started` | `CommandEventHandler?` | Raised immediately before the command method is invoked. |
| `Completed` | `CommandEventHandler?` | Raised when the command method returned successfully. |
| `Failed` | `CommandEventHandler?` | Raised when the command method threw a non-cancellation exception; `e.Exception` carries it. |
| `Canceled` | `CommandEventHandler?` | Raised when the execution was cancelled or refused. At most once per execution. |
| `Exited` | `CommandEventHandler?` | Raised when the execution finished and left the active set. Not raised for refused or cleared calls. |
| `CanExecuteChanged` | `EventHandler?` | Inherited from `ICommand`. |

##### Methods

###### `IVeloxCommand.ExecuteAsync`

**Signature:**
`Task ExecuteAsync(object? parameter)`

| Parameter | Type | Description |
|---|---|---|
| `parameter` | `object?` | The argument passed to the command body. |

**Returns:** `Task` — completes once the call has been **accepted** (started or queued), not when the body finishes.

**Exceptions:** none declared by the interface.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs, lines 141-147
private static async Task RunToCompletionAsync(IVeloxCommand command, object? parameter = null)
{
    var exited = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
    command.Exited += _ => exited.TrySetResult(true);
    await command.ExecuteAsync(parameter);
    await exited.Task.WaitAsync(CommandTestKit.Timeout);
}
```

**Notes:** to act on the result, subscribe to `Completed` / `Failed` / `Exited`, or use `ExecuteAndWaitAsync`.

###### `IVeloxCommand.Lock` / `LockAsync`

**Signature:**
`void Lock()` — `Task LockAsync()`

**Returns:** `Task` (async form) — completes once the force-lock is set.

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 158-167
private void FreeCommand()
{
    MinusCommand.Lock();   // enter the locked state: prevents new commands from triggering but
                           // does not interrupt the currently running command

    MinusCommand.Interrupt();    // interrupt the current command
    MinusCommand.Clear();        // interrupt the current command and all queued commands

    MinusCommand.Unlock(); // release the lock
}
```

**Notes:** `CanExecute` returns `false` while locked, and new requests are refused (raising `Created` then `Canceled`). Running work is untouched. A command that is already locked stays locked after `Interrupt` / `Clear`.

###### `IVeloxCommand.Unlock` / `UnlockAsync`

**Signature:**
`void Unlock()` — `Task UnlockAsync()`

**Returns:** `Task` (async form) — completes once the lock is released and the queue has been drained as far as capacity allows.

**Notes:** the member is spelled `Unlock`. It exists on the interface, so it is forwarded by *both* `VeloxCommand` and generated command properties.

###### `IVeloxCommand.Notify`

**Signature:**
`void Notify()`

**Returns:** `void` — raises `CanExecuteChanged`.

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 34-37
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}
```

**Notes:** call it whenever the `CanExecute{Name}Command` predicate's result may have changed. A throwing `CanExecuteChanged` subscriber is swallowed and reported through `VeloxCommand.HandlerException`.

###### `IVeloxCommand.Interrupt` / `InterruptAsync`

**Signature:**
`void Interrupt()` — `Task InterruptAsync()`

**Returns:** `Task` (async form) — completes once the active executions have been cancelled and the command is back to its prior lock state.

**Notes:** cancels the running executions and raises `Canceled` for each. Queued items are left in the queue. A command that was not locked is unlocked again afterwards; one that was already locked stays locked.

###### `IVeloxCommand.Clear` / `ClearAsync`

**Signature:**
`void Clear()` — `Task ClearAsync()`

**Returns:** `Task` (async form) — completes once the queue is emptied and the active executions have been cancelled.

**Notes:** raises `Dequeued` for every pending item first, then `Canceled` for pending and active items alike. A pending item dropped this way never reaches `Started` / `Exited`.

###### `IVeloxCommand.Continue` / `ContinueAsync`

**Signature:**
`void Continue()` — `Task ContinueAsync()`

**Returns:** `Task` (async form).

**Notes:** starts queued work if the command is not force-locked; otherwise a no-op. Dirtying the queue after a `Clear` that left nothing pending starts nothing.

###### `IVeloxCommand.ChangeSemaphore` / `ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int semaphore)` — `Task ChangeSemaphoreAsync(int semaphore)`

| Parameter | Type | Description |
|---|---|---|
| `semaphore` | `int` | The new maximum number of concurrent executions. |

**Returns:** `Task` (async form).

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentOutOfRangeException` | `semaphore` is less than 1. The synchronous form validates before dispatching so the failure is not lost as an unobserved exception. |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs, lines 119-122
await command.ChangeSemaphoreAsync(3);

await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount, "raising the cap is what releases the queue - nothing else will");
```

**Notes:** raising the cap immediately drains whatever the queue can now hold.
