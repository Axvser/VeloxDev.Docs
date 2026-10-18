# MVVM — `VeloxCommand` construction

Every way to build a `VeloxCommand`. The choice decides two things: whether the body receives a per-execution `CancellationToken`, and whether its return value is captured for `IVeloxCommandResult`.

A body that never receives a token still reports `Canceled` when interrupted; it just cannot stop, so it runs on to completion.

###### `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

The primary constructor. The body receives both the parameter and a per-execution token.

| Parameter | Type | Description |
| --- | --- | --- |
| `command` | `Func<object?, CancellationToken, Task>` | The body to invoke. |
| `canExecute` | `Predicate<object?>?` | Executability predicate; `null` means always executable. |
| `semaphore` | `int` | Maximum concurrent executions. Must be ≥ 1. Default `1`. |

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `ArgumentNullException` | `command` is `null`. |
| `ArgumentOutOfRangeException` | `semaphore` is less than 1. |

###### `VeloxCommand(Func<Task> command, …)` / `VeloxCommand(Action<object?> command, …)` / `VeloxCommand(Action command, …)`

Bodies that never receive a token. Same `canExecute` and `semaphore` contract; the same `ArgumentOutOfRangeException` for a capacity below 1. A `null` body is not checked at construction: the wrapper that is passed to the base is non-null, so it surfaces as a `NullReferenceException` when an execution reaches it.

###### `VeloxCommand.CreateTaskOnlyWithParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** a command that awaits `command(parameter)`; the body never receives a token.

**Exceptions:** `ArgumentOutOfRangeException` when `semaphore < 1`.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
object? received = null;
var command = VeloxCommand.CreateTaskOnlyWithParameter(p =>
{
    received = p;
    return Task.CompletedTask;
});
var recorder = new CommandEventRecorder(command);

command.Execute("test");
await recorder.FirstExit;

Assert.AreEqual("test", received);
```

###### `VeloxCommand.CreateTaskOnlyWithCancellationToken`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** a command that awaits `command(ct)`; a token is created per execution, so the body really can be cancelled.

###### `VeloxCommand.CreateTaskOnlyWithResult`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithResult(Func<object?, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** a command whose body receives the parameter, returns a value, and never receives a token. The value is what `IVeloxCommandResult.ExecuteAsync(object?, CancellationToken)` hands back.

###### `VeloxCommand.CreateTaskWithResult`

**Signature:**
`static VeloxCommand CreateTaskWithResult(Func<object?, CancellationToken, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** the cancellable twin of `CreateTaskOnlyWithResult`.

###### `VeloxCommand.CreateTypedTaskOnlyWithParameter<T>`

**Signature:**
`static VeloxCommand<T, object?> CreateTypedTaskOnlyWithParameter<T>(Func<T, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)`

**Returns:** a typed command whose body receives `T` and no token. Used by the generator for a single typed parameter with no return value.

###### `VeloxCommand.CreateTypedWithParameter<T>`

**Signature:**
`static VeloxCommand<T, object?> CreateTypedWithParameter<T>(Func<T, CancellationToken, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)`

**Returns:** a typed command whose body receives `T` and the execution's token.

**Exceptions:** `ArgumentNullException` when `command` is `null` (this factory passes the body straight to the base constructor).

###### `VeloxCommand.CreateTaskOnlyWithValueTaskParameter` / `CreateTaskOnlyWithValueTaskCancellationToken`

**Signatures:**
`static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, …)`
`static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, …)`

**Returns:** the `ValueTask` twins of `CreateTaskOnlyWithParameter` and `CreateTaskOnlyWithCancellationToken`.

**Notes:**

- **Conditionally compiled:** present only under `#if !NETSTANDARD2_0 && !NETFRAMEWORK`.
- They are *named* factories rather than overloads: a `Func<object?, ValueTask>` beside `Func<object?, Task>` would make every `async` lambda call site ambiguous (`CS0121`).

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var gate = new CommandGate();
var command = VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken(
    ct => new ValueTask(gate.RunWithTokenAsync(ct)));
var recorder = new CommandEventRecorder(command);

_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();
await CommandTestKit.WaitUntilAsync(() => recorder.ExitCount >= 1);

Assert.HasCount(0, recorder.Of(CommandEventType.Failed));
```

## Generated call sites

The Command generator does not use the `ValueTask` factories: it emits an `.AsTask()` thunk, so the generated code works on every target framework. For a typed parameter it uses the typed factories:

```csharp
// Source: generated — *_Commands.g.cs (shape pinned by CommandSignatureDiagnosticsTests)
_buffer_SaveCommand ??= global::VeloxDev.MVVM.VeloxCommand<string, global::System.Object?>
    .CreateTypedTaskOnlyWithParameter<global::System.String>(
        command: Save,
        canExecute: _ => true,
        semaphore: 1);
```

**Notes:**

- The attribute's `semaphore` is passed through `Math.Max(1, semaphore)`, so generated commands never take the `ArgumentOutOfRangeException` path.
- A command built from a body without a token allocates no `CancellationTokenSource`, so its internal `Cts` is `null` and there is nothing to dispose.
