# Command Runtime

The bounded, queued, cancellable command pipeline behind every generated command. Direct use is fully supported when a command is constructed in code rather than generated.

## VeloxDev.MVVM

### Enum: CommandOutcome

| Member | Value | Meaning |
|---|---|---|
| `Completed` | 0 | The body ran to completion without throwing. |
| `Failed` | 1 | The body threw. |
| `Canceled` | 2 | Cancelled by `Interrupt` / `Clear`, by the body honouring its token, or dropped from the queue. |
| `Refused` | 3 | The call never ran because the command was locked. |

### Struct: CommandCompletion

The per-execution result returned by `ExecuteAndWaitAsync`.

**Signature:** `public readonly struct CommandCompletion`

| Member | Type | Description |
|---|---|---|
| `Outcome` | `CommandOutcome` | How the execution ended. |
| `Exception` | `Exception?` | The failure, on `Failed` only. |
| `Result` | `object?` | The body's value, boxed; `null` when it returned none. |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`. |

| Method | Signature | Description |
|---|---|---|
| `GetResultOrThrow` | `object? GetResultOrThrow()` | Returns `Result`, or throws the failure, `OperationCanceledException` for `Canceled`, or `InvalidOperationException` for `Refused`. |
| `GetResultOrThrow<TR>` | `TR GetResultOrThrow<TR>()` | The typed form; may throw `InvalidCastException`. |
| `ToString` | `string ToString()` | The outcome, plus the failure message when present. |

### Enum: CommandEventType

`None`, `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`.

`Exited` means only that the execution left the pipeline; it is not a success signal. `Failed` is the only stage that carries an exception.

### Delegate: CommandEventHandler

`public delegate void CommandEventHandler(CommandEventArgs e)`

### Class: CommandEventArgs

**Signature:** `public class CommandEventArgs(object? parameter, CommandEventType type, Exception? ex = null, CancellationTokenSource? cts = null)`

| Member | Type | Description |
|---|---|---|
| `Parameter` | `virtual object?` | The argument passed to `ICommand.Execute`; reading it boxes a value type. |
| `Exception` | `Exception?` | Populated on `Failed` only. |
| `EventType` | `CommandEventType` | The stage this instance reports. |

`With(CommandEventType newType, Exception? ex = null)` projects the same execution onto another stage while keeping the parameter and cancellation source.

### Class: CommandEventArgs<TParam, TResult>

The typed payload, deriving from `CommandEventArgs`.

**Signature:** `public sealed class CommandEventArgs<TParam, TResult> : CommandEventArgs`

| Member | Type | Description |
|---|---|---|
| `TypedParameter` | `TParam` | The argument in its own type; throws `InvalidCastException` if it arrived boxed as something else. |
| `TypedResult` | `TResult` | The body's value once the execution finished. |
| `Parameter` | `override object?` | The typed argument, boxed only when read. |
| `With` | `new CommandEventArgs<TParam, TResult> With(CommandEventType newType, Exception? ex = null)` | Projects the typed payload onto another stage. |

### Delegate: CommandEventHandler<TParam, TResult>

`public delegate void CommandEventHandler<TParam, TResult>(CommandEventArgs<TParam, TResult> e)`

### Class: CommandPipeline<TParam, TResult>

The shared implementation. Abstract; derive from it or use `VeloxCommand` / `VeloxCommand<TParam, TResult>`.

**Signature:**
`public abstract class CommandPipeline<TParam, TResult> : IVeloxCommand, IVeloxCommandCompletion, IVeloxCommandStatus, IVeloxCommandResult, IVeloxCommandEvents<TParam, TResult>, IDisposable`

**Constructor (protected)**
`CommandPipeline(Func<TParam, CancellationToken, Task> command, Func<TParam, CancellationToken, Task<TResult>>? resultCommand, Predicate<TParam>? canExecute, int semaphore, bool isCtsNeeded)`

**Events**

| Member | Signature | Description |
|---|---|---|
| `HandlerException` | `static event Action<Exception>?` | Reports a subscriber that threw. Process-wide, not per generic closure. |
| `CanExecuteChanged` | `event EventHandler?` | Standard `ICommand` notification. |
| `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited` | `event CommandEventHandler?` | The eight lifecycle stages. |

**Properties**

| Member | Type | Description |
|---|---|---|
| `EventContext` | `SynchronizationContext?` | When set, lifecycle events are posted there; `null` raises on the pipeline thread. |
| `IsBusy` | `bool` | An execution is running or queued. |
| `ActiveCount` | `int` | Executions running now. |
| `PendingCount` | `int` | Calls waiting for a slot. |

**Methods**

| Member | Signature | Description |
|---|---|---|
| `CanExecute` | `bool CanExecute(object? parameter)` | The `ICommand` face; never throws for a wrong-typed argument. |
| `Execute` | `void Execute(object? parameter)` | Starts an execution; returns once accepted. |
| `Notify` | `void Notify()` | Raises `CanExecuteChanged`. |
| `Lock` / `Unlock` | `void Lock()`, `void Unlock()` | Refuses / re-enables executions. |
| `Interrupt` | `void Interrupt()` | Cancels running executions, leaves the queue. |
| `Clear` | `void Clear()` | Cancels running and drops queued executions. |
| `Continue` | `void Continue()` | Starts queued work when not locked. |
| `ChangeSemaphore` | `void ChangeSemaphore(int s)` | Changes the concurrency cap; throws `ArgumentOutOfRangeException` when `s < 1`. |
| `ExecuteAsync` | `Task ExecuteAsync(object? parameter)` | Starts an execution. |
| `ExecuteAsync` | `Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)` | Waits for this execution and returns its boxed value. |
| `Execute` | `void Execute(object? parameter, out object? result)` | Blocking typed-result form. |
| `ExecuteAndWaitAsync` | `Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)` | Reports how this execution ended, including refused and dropped calls. |
| `LockAsync` / `UnlockAsync` / `InterruptAsync` / `ClearAsync` / `ContinueAsync` / `ChangeSemaphoreAsync` | `Task` | Awaitable counterparts. |
| `Dispose` | `void Dispose()` | Releases the internal lock; final. |

**Protected members:** `CanExecuteCore(TParam)`, `ExecuteAsyncCore(TParam)`, `ExecuteAndWaitTypedAsync(TParam, CancellationToken)`, `ExecuteAndWaitTyped(TParam)`.

### Class: VeloxCommand

The `object?`-shaped command.

**Signature:** `public class VeloxCommand : CommandPipeline<object?, object?>`

**Constructors**

| Signature |
|---|
| `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)` |

**Static factories**

| Member | Signature |
|---|---|
| `CreateTaskOnlyWithResult` | `static VeloxCommand CreateTaskOnlyWithResult(Func<object?, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskWithResult` | `static VeloxCommand CreateTaskWithResult(Func<object?, CancellationToken, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithParameter` | `static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTypedTaskOnlyWithParameter<T>` | `static VeloxCommand<T, object?> CreateTypedTaskOnlyWithParameter<T>(Func<T, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)` |
| `CreateTypedWithParameter<T>` | `static VeloxCommand<T, object?> CreateTypedWithParameter<T>(Func<T, CancellationToken, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithValueTaskParameter` | `static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)` (not `netstandard2.0` / `netframework`) |
| `CreateTaskOnlyWithValueTaskCancellationToken` | `static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)` (not `netstandard2.0` / `netframework`) |

### Class: VeloxCommand<TParam, TResult>

The one-parameter typed command.

**Signature:** `public sealed class VeloxCommand<TParam, TResult> : CommandPipeline<TParam, TResult>, IVeloxCommand<TParam, TResult>`

**Constructor**
`public VeloxCommand(Func<TParam, CancellationToken, Task<TResult>> command, Predicate<TParam>? canExecute = null, int semaphore = 1)`

**Static factory**
`public static VeloxCommand<TParam, TResult> CreateTaskOnlyWithResult(Func<TParam, Task<TResult>> command, Predicate<TParam>? canExecute = null, int semaphore = 1)`

**Members:** `CanExecute(TParam)`, `Execute(TParam)`, `ExecuteAsync(TParam)`, `ExecuteAsync(TParam, CancellationToken)`, `Execute(TParam, out TResult)`.

## Multi-parameter command family

`CommandArities.cs` declares, for every parameter count 2 through 15, an interface and a sealed class:

- `IVeloxCommand<TParam1, …, TParamN, TResult>` deriving from `IVeloxCommand`
- `VeloxCommand<TParam1, …, TParamN, TResult>` deriving from `CommandPipeline<(TParam1, …, TParamN), TResult>`

Each interface declares `CanExecute(...)`, `Execute(...)`, `ExecuteAsync(...)`, `ExecuteAsync(..., CancellationToken)` and `Execute(..., out TResult)`. Each class has a constructor taking `Func<TParam1, …, TParamN, CancellationToken, Task<TResult>>`, an optional `Func<…, bool>` validator and an `int semaphore`, plus a `CreateTaskOnlyWithResult` factory and the same five members. The arguments travel through the pipeline as a `ValueTuple`, so no argument is boxed on the typed path. A command with no parameter has no typed form; use `VeloxCommand` (`object?`-shaped) or a body that ignores the argument.

## Exceptions

| Exception | Condition |
|---|---|
| `ArgumentNullException` | A command body is `null`. |
| `ArgumentOutOfRangeException` | `semaphore < 1` on construction or `ChangeSemaphore`; a negative rate on a transition is unrelated. |
| `OperationCanceledException` | The caller's `CancellationToken` abandons a wait, or a waited execution was cancelled. |
| `InvalidOperationException` | A waited execution was refused because the command was locked. |

## Example

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.MVVM;

var save = new VeloxCommand(
    async (object? _, CancellationToken ct) => await Task.Delay(50, ct),
    semaphore: 1);

await save.ExecuteAsync(null);
CommandCompletion how = await save.ExecuteAndWaitAsync(null);
Console.WriteLine(how.Outcome);
```

The generated command property is declared as the interface (`IVeloxCommand`), so this example constructs the concrete type explicitly. See [MVVM ViewModel Generation](../../../1_QuickStart/11_mvvm-viewmodel-generation/index.md) for the attribute-driven path.
