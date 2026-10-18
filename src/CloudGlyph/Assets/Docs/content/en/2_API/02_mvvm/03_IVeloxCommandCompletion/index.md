# MVVM — `IVeloxCommandCompletion`

`VeloxDev.MVVM.IVeloxCommandCompletion` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandCompletion.cs`) is a command that can report when one specific execution has ended. It is implemented by `VeloxCommand` (through `CommandPipeline<TParam, TResult>`) and reached from an `IVeloxCommand` through `VeloxCommandExtensions`.

## Interface: `IVeloxCommandCompletion`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandCompletion
{
    Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default);
}
```

It declares exactly one member; it inherits nothing.

**Why it is separate:** `IVeloxCommand.ExecuteAsync` returns as soon as the call is accepted, which leaves callers pairing `Exited` with `Failed` by hand. That pairing never completes for a refused or dropped call, because those never raise `Exited`. A separate interface means adding it broke no existing implementer.

##### Methods

###### `IVeloxCommandCompletion.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| Parameter | Type | Description |
| --- | --- | --- |
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons **the wait only** — it does not cancel the execution. Use `Interrupt` or `Clear` to stop work already under way. Optional. |

**Returns:** `Task<CommandCompletion>` — how *this* execution ended. A cancelled execution is a normal return with `Outcome == CommandOutcome.Canceled`.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `OperationCanceledException` | `cancellationToken` fired first. |

**Example:**

```csharp
// Source: Demo/test usage — recorded semantics in Quick Start
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var running = command.ExecuteAndWaitAsync(null, cts.Token);
await gate.WaitForStartedAsync();

cts.Cancel();

await Assert.ThrowsAsync<OperationCanceledException>(() => running);

Assert.AreEqual(1, command.ActiveCount(), "cancelling the wait must not touch the execution");
```

**Notes:**

- A call still queued while the command stays locked has not ended, so the returned task does not complete until a slot frees or the queue is cleared.
- `CommandCompletion` reports four outcomes, including `Refused`, and carries the body's value in `Result`. For the untyped result API see `15_IVeloxCommandResult`; for the typed one see `16_typed-commands`.
- On an `IVeloxCommand` reference, use `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, …)`; a hand-written implementation that omits this interface makes that extension throw `NotSupportedException`.
