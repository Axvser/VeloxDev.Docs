# MVVM — `CommandCompletion`

`VeloxDev.MVVM.CommandCompletion` (`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`) is the result of one execution, as returned by `ExecuteAndWaitAsync`.

## Struct: `CommandCompletion`

**Signature**

```csharp
public readonly struct CommandCompletion(CommandOutcome outcome, Exception? exception = null)
{
    public CommandOutcome Outcome { get; } = outcome;
    public Exception? Exception { get; } = exception;

    public bool Succeeded => Outcome == CommandOutcome.Completed;

    public override string ToString() =>
        Exception is null ? Outcome.ToString() : $"{Outcome}: {Exception.Message}";
}
```

- **Kind:** `readonly struct` (a value type; no `null` state).
- **Constructor:** the public primary one, `(CommandOutcome outcome, Exception? exception = null)`.

Unlike the lifecycle events, this is **per-call**: it answers "how did *this* execution end", including for the calls that never run at all. That is what makes it usable as an await.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Outcome` | `CommandOutcome` | How the execution ended. |
| `Exception` | `Exception?` | The failure, on `CommandOutcome.Failed` only; otherwise `null`. |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`. |

##### Methods

###### `CommandCompletion.ToString`

**Signature:**
`override string ToString()`

**Returns:** `string` — the outcome name, or `"{Outcome}: {Exception.Message}"` when there is a failure.

**Example:**

```csharp
// Source: Inferred from the declaration (Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs, lines 57-58)
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.ToString());   // "Completed", or e.g. "Failed: boom"
```

**Notes:** this makes a `CommandCompletion` safe to interpolate into a log line — an exception message is appended only when there is one.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 15-25
var command = new VeloxCommand(() => Task.CompletedTask);

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Completed, completion.Outcome);
Assert.IsTrue(completion.Succeeded);
Assert.IsNull(completion.Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 44-56
var boom = new InvalidOperationException("boom");
var command = new VeloxCommand((_, _) => Task.FromException(boom));

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.AreSame(boom, completion.Exception);
Assert.IsFalse(completion.Succeeded);
```

## Notes

- A cancelled execution is a **normal return**, not a thrown exception — `Outcome` is `CommandOutcome.Canceled`. Only the caller's own `CancellationToken` aborts the wait, and that does throw `OperationCanceledException`.
- The value is a struct, so it carries no allocation of its own; the only allocation on this path is the `TaskCompletionSource` the awaiting call creates.
- `Outcome` is computed from the execution itself, not read back from the events, so a `Failed` result does not depend on anyone having subscribed to `Failed`.
