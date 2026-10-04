# MVVM — `VeloxCommand` construction

Every way to build a `VeloxCommand`. Which one you get determines only whether the body receives a per-execution `CancellationToken` — everything else (queueing, lifecycle events, interruption reporting) is identical.

A body that never receives a token still reports `Canceled` when interrupted; it just has no way to actually stop, so it runs on to completion. That distinction is recorded internally by `_isCtsNeeded`.

###### `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

The primary constructor. Creates a command whose body receives both the parameter and a per-execution cancellation token.

| Parameter | Type | Description |
|---|---|---|
| `command` | `Func<object?, CancellationToken, Task>` | The body to invoke. |
| `canExecute` | `Predicate<object?>?` | Executability predicate; when `null`, the command is always executable. Optional. |
| `semaphore` | `int` | Maximum concurrent executions. Must be ≥ 1. Optional, default `1`. |

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentNullException` | `command` is `null`. |
| `ArgumentOutOfRangeException` | `semaphore` is less than 1. |

###### `VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

Creates a command from a body that takes nothing. The body never receives a token, so an interrupted execution reports `Canceled` without the body actually stopping.

**Exceptions:** as the primary constructor.

###### `VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

Creates a command from a synchronous body that takes the parameter. The body never receives a token.

**Exceptions:** as the primary constructor.

###### `VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)`

Creates a command from a synchronous body that takes nothing.

**Exceptions:** as the primary constructor.

###### `VeloxCommand.CreateTaskOnlyWithParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

| Parameter | Type | Description |
|---|---|---|
| `command` | `Func<object?, Task>` | The body, taking the parameter only. |
| `canExecute` | `Predicate<object?>?` | Executability predicate. Optional. |
| `semaphore` | `int` | Concurrency cap, ≥ 1. Optional, default `1`. |

**Returns:** `VeloxCommand` — a command that awaits `command(parameter)`; the body never receives a token.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `ArgumentOutOfRangeException` when `semaphore < 1`.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 86-100
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

**Returns:** `VeloxCommand` — a command that awaits `command(ct)`; a token is created per execution, so the body really can be cancelled.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `ArgumentOutOfRangeException` when `semaphore < 1`.

###### `VeloxCommand.CreateTaskOnlyWithValueTaskParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** `VeloxCommand` — as `CreateTaskOnlyWithParameter`, for a `ValueTask`-returning body. The body never receives a token.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `ArgumentOutOfRangeException` when `semaphore < 1`.

**Notes:**

- **Conditionally compiled:** present only under `#if !NETSTANDARD2_0 && !NETFRAMEWORK`, so it does not exist on the `netstandard2.0` or `netframework4.6.1` targets.
- It is a *named* factory rather than an overload of `CreateTaskOnlyWithParameter`. A `Func<object?, ValueTask>` next to the `Func<object?, Task>` one would make every `async` lambda call site ambiguous (`CS0121`), and `async p => { … }` is how callers write commands.

###### `VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** `VeloxCommand` — as `CreateTaskOnlyWithCancellationToken`, for a `ValueTask`-returning body. A token is created per execution.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `ArgumentOutOfRangeException` when `semaphore < 1`.

**Notes:** same `#if !NETSTANDARD2_0 && !NETFRAMEWORK` guard as `CreateTaskOnlyWithValueTaskParameter`.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 119-135
var gate = new CommandGate();
var command = VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken(
    ct => new ValueTask(gate.RunWithTokenAsync(ct)));
var recorder = new CommandEventRecorder(command);

_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();
await CommandTestKit.WaitUntilAsync(() => recorder.ExitCount >= 1);

Assert.HasCount(0, recorder.Of(CommandEventType.Failed),
    "a ValueTask body that honours the token is cancelled, not failed");
```

## Generated call sites

The Command generator does not use the `ValueTask` factories at all — it emits a `.AsTask()` conversion thunk instead, so the generated code works on every target framework:

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs
_buffer_SumToCommand ??= global::VeloxDev.MVVM.VeloxCommand.CreateTaskOnlyWithParameter(
    command: parameter => SumToAsync((int)parameter!).AsTask(),
    canExecute: _ => true,
    semaphore: 1);
```

**Notes:**

- The attribute's `semaphore` is passed through `Math.Max(1, semaphore)` by the writer, so generated commands never take the `ArgumentOutOfRangeException` path; only a hand-written construction can.
- A command built from a body without a token hands out no `CancellationTokenSource`, so `CommandEventArgs.Cts` (internal) is `null` for it — and there is nothing to dispose.
