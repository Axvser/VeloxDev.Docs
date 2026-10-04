# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) enumerates the lifecycle state of one command execution. It is the type of `CommandEventArgs.EventType`.

## Enum: `CommandEventType`

**Signature**

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,   // Created
    Enqueued,  // Enqueued, waiting to run
    Dequeued,  // Dequeued, ready to execute
    Started,   // Execution actually started
    Completed, // Executed successfully
    Failed,    // Execution failed
    Canceled,  // Cancelled
    Exited     // Lifecycle ended
}
```

##### Fields

| Name | Value | Description |
|---|---|---|
| `None` | `0` | Unset / default. Never raised by `VeloxCommand`. |
| `Created` | `1` | A request was accepted and its payload allocated. |
| `Enqueued` | `2` | The concurrency cap was reached; the execution waits in the pending queue. |
| `Dequeued` | `3` | The queued execution left the queue and is about to run. |
| `Started` | `4` | The command method actually started. |
| `Completed` | `5` | The command method returned successfully. |
| `Failed` | `6` | The command method threw a non-cancellation exception. |
| `Canceled` | `7` | The execution was cancelled, or refused by a lock. |
| `Exited` | `8` | The lifecycle ended; the execution left the active set. |

## Sequences

An execution that runs immediately reports `Created`, `Started`, `Completed` and `Exited`. One that had to wait for a free slot reports `Enqueued` and `Dequeued` around that same sequence. One that was refused by a lock, or that was interrupted, reports `Canceled` in place of `Completed`; one whose body threw reports `Failed`.

A stage can have more than one emitter, so the same value may arrive twice for one execution: `Canceled` is raised by `Interrupt` and `Clear` as well as by the body's own `OperationCanceledException`. `RaiseCanceled` guards this with `TryMarkCancelReported()`, so at most one `Canceled` per execution reaches a handler.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs, lines 44-56
var command = new VeloxCommand(() => Task.CompletedTask);
var recorder = new CommandEventRecorder(command);

await command.ExecuteAsync(null);
await recorder.FirstExit;

CollectionAssert.AreEqual(
    new[] { CommandEventType.Created, CommandEventType.Started, CommandEventType.Completed, CommandEventType.Exited },
    recorder.Types);
```

## Notes

- **No member corresponds to `CommandOutcome.Refused`.** A refused execution reports `Canceled` and never reaches `Exited`, so this enum alone cannot tell a refusal apart from a cancellation. `ExecuteAndWaitAsync` is the only way to observe a refusal. See the `10_CommandOutcome` page.
- `None = 0` exists so a default-initialized value is distinguishable from every real stage.
- `Exited` is not a success signal: `CommandEventArgs.Exception` is populated on `Failed` only, and stays `null` on `Exited`.
