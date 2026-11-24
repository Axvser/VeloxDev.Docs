# Command Interfaces

The interface split lets a command stay bindable while optional capabilities remain additive. Every generated command is returned as one of these interfaces.

## VeloxDev.MVVM

### Interface: IVeloxCommand

The bindable base. Extends `System.Windows.Input.ICommand`.

**Signature:** `public interface IVeloxCommand : ICommand`

**Events**

| Member | Signature | Description |
|---|---|---|
| `Created` | `event CommandEventHandler?` | The call was accepted. |
| `Enqueued` | `event CommandEventHandler?` | The call was parked waiting for a free slot. |
| `Dequeued` | `event CommandEventHandler?` | A parked call left the queue and started. |
| `Started` | `event CommandEventHandler?` | The body began running. |
| `Completed` | `event CommandEventHandler?` | The body completed without throwing. |
| `Failed` | `event CommandEventHandler?` | The body threw. |
| `Canceled` | `event CommandEventHandler?` | The execution was cancelled. |
| `Exited` | `event CommandEventHandler?` | The execution left the pipeline, however it ended. |

**Methods**

| Member | Signature | Description |
|---|---|---|
| `Lock` | `void Lock()` | Refuses new executions and parks the queue. |
| `Unlock` | `void Unlock()` | Re-enables the command and starts queued work. |
| `Notify` | `void Notify()` | Raises `CanExecuteChanged`. |
| `Clear` | `void Clear()` | Cancels running executions and drops queued ones. |
| `Interrupt` | `void Interrupt()` | Cancels running executions, leaving the queue. |
| `Continue` | `void Continue()` | Starts queued work when not locked. |
| `ChangeSemaphore` | `void ChangeSemaphore(int semaphore)` | Changes the concurrency cap. |
| `ExecuteAsync` | `Task ExecuteAsync(object? parameter)` | Starts an execution; returns once accepted. |
| `LockAsync` | `Task LockAsync()` | Awaitable `Lock`. |
| `UnlockAsync` | `Task UnlockAsync()` | Awaitable `Unlock`. |
| `ClearAsync` | `Task ClearAsync()` | Awaitable `Clear`. |
| `InterruptAsync` | `Task InterruptAsync()` | Awaitable `Interrupt`. |
| `ContinueAsync` | `Task ContinueAsync()` | Awaitable `Continue`. |
| `ChangeSemaphoreAsync` | `Task ChangeSemaphoreAsync(int semaphore)` | Awaitable `ChangeSemaphore`. |

### Interface: IVeloxCommand<TParam, TResult>

Typed overloads on top of `IVeloxCommand`. Deriving from it keeps the command bindable.

**Signature:** `public interface IVeloxCommand<TParam, TResult> : IVeloxCommand`

| Member | Signature | Description |
|---|---|---|
| `CanExecute` | `bool CanExecute(TParam parameter)` | Reflects the predicate and the lock, never the queue. |
| `Execute` | `void Execute(TParam parameter)` | Starts an execution. |
| `ExecuteAsync` | `Task ExecuteAsync(TParam parameter)` | Starts an execution. |
| `ExecuteAsync` | `Task<TResult> ExecuteAsync(TParam parameter, CancellationToken cancellationToken)` | Waits for this execution and returns its value. |
| `Execute` | `void Execute(TParam parameter, out TResult result)` | Blocking form; deadlocks if called from the same command's body. |

The arity family adds `IVeloxCommand<TParam1, …, TParamN, TResult>` for 2–15 parameters, each with the same five members.

### Interface: IVeloxCommandStatus

Read-only queue state, which `CanExecute` cannot express.

**Signature:** `public interface IVeloxCommandStatus`

| Member | Type | Description |
|---|---|---|
| `IsBusy` | `bool` | An execution is running or queued. |
| `ActiveCount` | `int` | Executions running now. |
| `PendingCount` | `int` | Calls waiting for a slot. |

### Interface: IVeloxCommandResult

Returns the value a body produced.

**Signature:** `public interface IVeloxCommandResult`

| Member | Signature | Description |
|---|---|---|
| `ExecuteAsync` | `Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)` | Waits for this execution; the boxed body value. |
| `Execute` | `void Execute(object? parameter, out object? result)` | Blocking form. |

The `CancellationToken` parameter deliberately has no default, so the one-argument `IVeloxCommand.ExecuteAsync` is never ambiguous.

### Interface: IVeloxCommandCompletion

Reports how one specific execution ended, including refused and dropped calls.

**Signature:** `public interface IVeloxCommandCompletion`

| Member | Signature | Description |
|---|---|---|
| `ExecuteAndWaitAsync` | `Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)` | Completes when this execution ended, or when the caller's token fires. |

### Interface: IVeloxCommandEvents<TParam, TResult>

The typed lifecycle events, implemented explicitly so the `object?`-shaped events keep the class-level names. Subscribe through a reference typed as this interface to receive unboxed payloads.

**Signature:** `public interface IVeloxCommandEvents<TParam, TResult>`

Members: `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`, all `event CommandEventHandler<TParam, TResult>?`.

### Class: VeloxCommandExtensions

Reaches the optional capabilities from the interface type a generated property is declared with.

**Signature:** `public static class VeloxCommandExtensions`

| Member | Signature | Description |
|---|---|---|
| `ExecuteAndWaitAsync` | `static Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default)` | Throws `NotSupportedException` when the instance does not implement `IVeloxCommandCompletion`. |
| `IsBusy` | `static bool IsBusy(this IVeloxCommand command)` | Throws `NotSupportedException` when `IVeloxCommandStatus` is missing. |
| `ActiveCount` | `static int ActiveCount(this IVeloxCommand command)` | Same condition. |
| `PendingCount` | `static int PendingCount(this IVeloxCommand command)` | Same condition. |

All four throw `ArgumentNullException` for a `null` command.

## Example

```csharp
using System;
using VeloxDev.MVVM;

IVeloxCommand command = note.PromoteCommand;

Console.WriteLine(command.IsBusy());                 // extension over IVeloxCommandStatus
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.Outcome);               // Completed / Canceled / Refused
```

## Notes

- The optional interfaces exist separately so adding a capability never breaks a hand-written `IVeloxCommand` implementation; `net461` and `netstandard2.0` have no default interface members to soften an addition.
- A typed command is still reachable through the inherited `object?` overloads, so passing the wrong type compiles and ends as a `CommandOutcome.Failed` execution carrying an `InvalidCastException`.
