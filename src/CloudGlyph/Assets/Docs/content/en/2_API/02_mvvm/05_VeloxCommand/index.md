# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the sealed concrete implementation of `IVeloxCommand`, `IVeloxCommandCompletion` and `IVeloxCommandStatus`, and additionally implements `IDisposable`. It is the only type the Command generator ever constructs.

## Class: `VeloxCommand`

**Signature**

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand, IVeloxCommandCompletion, IVeloxCommandStatus, IDisposable
```

**Implements:** `IVeloxCommand` (which extends `System.Windows.Input.ICommand`), `IVeloxCommandCompletion`, `IVeloxCommandStatus`, `IDisposable`.

**Sealed:** yes.

## Member index

| Kind | Members | Page |
|---|---|---|
| Constructors | primary `(Func<object?, CancellationToken, Task>, …)`, `(Func<Task>, …)`, `(Action<object?>, …)`, `(Action, …)` | [Constructors](00_constructors/index.md) |
| Static factories | `CreateTaskOnlyWithParameter`, `CreateTaskOnlyWithCancellationToken`, `CreateTaskOnlyWithValueTaskParameter`, `CreateTaskOnlyWithValueTaskCancellationToken` | [Constructors](00_constructors/index.md) |
| Execution | `CanExecute`, `Execute`, `ExecuteAsync`, `ExecuteAndWaitAsync`, `Notify` | [Execution](01_execution/index.md) |
| Lifecycle control | `Lock` / `LockAsync`, `Unlock` / `UnlockAsync`, `Interrupt` / `InterruptAsync`, `Clear` / `ClearAsync`, `Continue` / `ContinueAsync`, `ChangeSemaphore` / `ChangeSemaphoreAsync` | [Lifecycle control](02_control/index.md) |
| Properties | `EventContext`, `IsBusy`, `ActiveCount`, `PendingCount` | [Status, events and teardown](03_status-events-and-disposal/index.md) |
| Events | 8 lifecycle events (`Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`), `CanExecuteChanged`, static `HandlerException` | [Status, events and teardown](03_status-events-and-disposal/index.md) |
| Teardown | `Dispose` | [Status, events and teardown](03_status-events-and-disposal/index.md) |

## Behaviour

- **Thread-safe.** All internal state (`_pendingQueue`, `_active`, `_isForceLocked`, `_maxConcurrency`) is guarded by a private `SemaphoreSlim(1,1)`, and every internal await uses `ConfigureAwait(false)`. No user code runs while that lock is held, so a handler that blocks on the command cannot deadlock it.
- **Bounded and queued.** `semaphore` is the concurrency cap. A call that cannot start immediately is enqueued rather than dropped, and starts when a slot frees.
- **Observable.** Each execution reports the eight `CommandEventType` stages through the matching events; `Execute` / `ExecuteAsync` return once the execution is accepted, not once it finishes.
- **Zero-cost when unobserved.** A stage with no subscriber does not build its `CommandEventArgs`, so a command with no subscribers allocates less per execution than one with every event subscribed (`CommandAllocationTests`).

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 19-29
var called = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
var command = new VeloxCommand(() => called.TrySetResult(true));
var recorder = new CommandEventRecorder(command);

command.Execute(null);
await recorder.FirstExit;

Assert.IsTrue(called.Task.IsCompleted, "the body ran to completion");
```

## Where it comes from

You rarely construct one by hand: `[VeloxCommand]` makes the Command generator emit a lazy property whose getter calls one of these constructors or factories (see the `14_Command` page). Direct construction is how the tests exercise the runtime, and how a view-model would build a command for a method it does not want to annotate.
