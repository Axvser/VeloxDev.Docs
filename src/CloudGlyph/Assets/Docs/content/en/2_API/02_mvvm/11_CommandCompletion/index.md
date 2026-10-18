# MVVM — `CommandCompletion`

`VeloxDev.MVVM.CommandCompletion` (`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`) is the result of one execution, as returned by `ExecuteAndWaitAsync`.

## Struct: `CommandCompletion`

**Signature**

```csharp
public readonly struct CommandCompletion(
    CommandOutcome outcome,
    Exception? exception = null,
    object? result = null)
{
    public CommandOutcome Outcome { get; } = outcome;
    public Exception? Exception { get; } = exception;
    public object? Result { get; } = result;

    public bool Succeeded => Outcome == CommandOutcome.Completed;

    public object? GetResultOrThrow();
    public TR GetResultOrThrow<TR>();
    public override string ToString() =>
        Exception is null ? Outcome.ToString() : $"{Outcome}: {Exception.Message}";
}
```

- **Kind:** `readonly struct` (a value type; no `null` state).
- **Constructor:** `(CommandOutcome outcome, Exception? exception = null, object? result = null)`.

Unlike the lifecycle events, this is **per-call**: it answers "how did *this* execution end", including calls that never run.

##### Properties

| Name | Type | Description |
| --- | --- | --- |
| `Outcome` | `CommandOutcome` | How the execution ended. |
| `Exception` | `Exception?` | The failure, on `CommandOutcome.Failed` only; otherwise `null`. |
| `Result` | `object?` | The body's value, boxed — `null` when it returned nothing or returned `null` itself. Only `Completed` carries a value. |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`. |

##### Methods

###### `CommandCompletion.GetResultOrThrow`

**Signature:**
`object? GetResultOrThrow()`

**Returns:** `Result`, boxed, or `null` when the body returned none.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `Exception` | the body threw; the original instance is rethrown through `ExceptionDispatchInfo`, so the stack trace survives |
| `OperationCanceledException` | the execution was cancelled |
| `InvalidOperationException` | the call was refused because the command was locked |

**Notes:** this is where a completion turns into a value. `ExecuteAndWaitAsync` itself deliberately reports outcomes without throwing.

###### `CommandCompletion.GetResultOrThrow<TR>`

**Signature:**
`TR GetResultOrThrow<TR>()`

**Returns:** `Result` cast to `TR`.

**Exceptions:** the same outcomes as the non-generic overload, plus `InvalidCastException` when `Result` is not a `TR`.

###### `CommandCompletion.ToString`

**Signature:**
`override string ToString()`

**Returns:** the outcome name, or `"{Outcome}: {Exception.Message}"` when there is a failure.

**Example:**

```csharp
// Source: Inferred from the declaration
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.ToString());   // "Completed", or e.g. "Failed: boom"
```

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Completed, completion.Outcome);
Assert.IsTrue(completion.Succeeded);
Assert.IsNull(completion.Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var boom = new InvalidOperationException("boom");
var command = new VeloxCommand((_, _) => Task.FromException(boom));

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.AreSame(boom, completion.Exception);
Assert.IsFalse(completion.Succeeded);
```

## Notes

- A cancelled execution is a **normal return**, not a thrown exception — `Outcome` is `CommandOutcome.Canceled`. Only the caller's own `CancellationToken` aborts the wait, and that does throw.
- The value is a struct, so it carries no allocation of its own; the only allocation on this path is the `TaskCompletionSource` the awaiting call creates.
- `Outcome` is computed from the execution itself, not read back from events, so a `Failed` result does not depend on anyone having subscribed to `Failed`.
