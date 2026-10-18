# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the `object?`-shaped command. It derives from `CommandPipeline<object?, object?>`, which supplies every interface and every member; `VeloxCommand` itself adds the constructors and factories that decide whether the body receives a token and whether its return value is captured.

## Class: `VeloxCommand`

**Signature**

```csharp
public class VeloxCommand : CommandPipeline<object?, object?>
{
    public VeloxCommand(
        Func<object?, CancellationToken, Task> command,
        Predicate<object?>? canExecute = null,
        int semaphore = 1);

    public VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1);
    public VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1);
    public VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1);
}
```

**Base type:** `CommandPipeline<object?, object?>`, from which it inherits `IVeloxCommand` (and therefore `ICommand`), `IVeloxCommandCompletion`, `IVeloxCommandResult`, `IVeloxCommandStatus`, `IVeloxCommandEvents<object?, object?>`, and `IDisposable`.

**Sealed:** no. The typed family (`VeloxCommand<TParam, TResult>` and the arity variants) is separate.

## Member index

| Kind | Members | Page |
| --- | --- | --- |
| Constructors | `(Func<object?, CancellationToken, Task>, …)`, `(Func<Task>, …)`, `(Action<object?>, …)`, `(Action, …)` | [Constructors](00_constructors/index.md) |
| Static factories | `CreateTaskOnlyWithResult`, `CreateTaskWithResult`, `CreateTaskOnlyWithParameter`, `CreateTaskOnlyWithCancellationToken`, `CreateTypedTaskOnlyWithParameter<T>`, `CreateTypedWithParameter<T>`, the two `ValueTask` factories (conditional) | [Constructors](00_constructors/index.md) |
| Execution | `CanExecute`, `Execute`, `ExecuteAsync(object?)`, `ExecuteAsync(object?, CancellationToken)`, `Execute(object?, out object?)`, `ExecuteAndWaitAsync`, `Notify` | [Execution](01_execution/index.md) |
| Lifecycle control | `Lock` / `LockAsync`, `Unlock` / `UnlockAsync`, `Interrupt` / `InterruptAsync`, `Clear` / `ClearAsync`, `Continue` / `ContinueAsync`, `ChangeSemaphore` / `ChangeSemaphoreAsync` | [Lifecycle control](02_control/index.md) |
| Properties | `EventContext`, `IsBusy`, `ActiveCount`, `PendingCount` | [Status, events and teardown](03_status-events-and-disposal/index.md) |
| Events | 8 lifecycle events, `CanExecuteChanged`, static `HandlerException`, the typed events (explicitly implemented) | [Status, events and teardown](03_status-events-and-disposal/index.md) |
| Teardown | `Dispose` | [Status, events and teardown](03_status-events-and-disposal/index.md) |

## Behaviour

- **Thread-safe.** Internal state is guarded by a private `SemaphoreSlim(1,1)`, and every internal await uses `ConfigureAwait(false)`. No user code runs while that lock is held.
- **Bounded and queued.** `semaphore` is the concurrency cap. A call that cannot start is enqueued rather than dropped.
- **Observable.** Each execution reports the eight `CommandEventType` stages; `Execute` / `ExecuteAsync` return once the execution is accepted.
- **Zero-cost when unobserved.** A stage with no subscriber does not build its `CommandEventArgs` (`CommandAllocationTests`).

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var called = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
var command = new VeloxCommand(() => called.TrySetResult(true));
var recorder = new CommandEventRecorder(command);

command.Execute(null);
await recorder.FirstExit;

Assert.IsTrue(called.Task.IsCompleted, "the body ran to completion");
```

## Where it comes from

You rarely construct one by hand: `[VeloxCommand]` makes the Command generator emit a lazy property whose getter calls one of these constructors or factories (see the `14_Command` page). Direct construction is how the tests exercise the runtime, and how a view-model builds a command for a method it does not want to annotate.
