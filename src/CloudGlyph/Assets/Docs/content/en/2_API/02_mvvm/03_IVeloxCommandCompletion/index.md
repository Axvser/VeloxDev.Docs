# MVVM — `IVeloxCommandCompletion`

`VeloxDev.MVVM.IVeloxCommandCompletion` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandCompletion.cs`) is a command that can report when one specific execution has ended. It is implemented by `VeloxCommand`, and reached from an `IVeloxCommand` through `VeloxCommandExtensions`.

## Interface: `IVeloxCommandCompletion`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandCompletion
{
    Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default);
}
```

It declares exactly one member; there is no inheritance.

**Why it is a separate interface:** `IVeloxCommand.ExecuteAsync` returns as soon as the call is accepted — queued or started — which leaves callers that need the actual result pairing `Exited` with `Failed` by hand. That pairing never completes for a call the command refuses or drops, because those never raise `Exited`. Making this a separate interface rather than a member of `IVeloxCommand` means adding it breaks no existing implementer.

##### Methods

###### `IVeloxCommandCompletion.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| Parameter | Type | Description |
|---|---|---|
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons **the wait only** — it does not cancel the execution. Use `Interrupt` or `Clear` to stop work already under way. Optional. |

**Returns:** `Task<CommandCompletion>` — how *this* execution ended. A cancelled execution is a normal return with `Outcome == CommandOutcome.Canceled`.

**Exceptions:**

| Exception | Condition |
|---|---|
| `OperationCanceledException` | `cancellationToken` fired first. |

**Example:**

```csharp
// Source: Demo — the recorded run of the Quick Start complete-code program
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 102-119
var running = command.ExecuteAndWaitAsync(null, cts.Token);
await gate.WaitForStartedAsync();

cts.Cancel();

await Assert.ThrowsAsync<OperationCanceledException>(() => running);

// abandoning the wait is not cancelling the execution: the body is still running, the slot still taken
Assert.AreEqual(1, command.ActiveCount(), "cancelling the wait must not touch the execution");
```

**Notes:**

- A call that is still queued while the command stays locked has not ended, so the returned task does not complete until a slot frees or the queue is cleared. Pass a `cancellationToken` if that wait needs an escape hatch.
- The result distinguishes four outcomes, including `CommandOutcome.Refused`, which the event stream cannot express. See the `10_CommandOutcome` and `11_CommandCompletion` pages.
- On an `IVeloxCommand` reference, use `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, …)`; a hand-written implementation that does not implement this interface makes that extension throw `NotSupportedException`.
