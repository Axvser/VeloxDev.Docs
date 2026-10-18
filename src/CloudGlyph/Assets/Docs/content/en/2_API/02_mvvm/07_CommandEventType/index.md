# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType` (`Src/Core/VeloxDev.Core/MVVM/CommandEventType.cs`) enumerates the lifecycle state of one command execution. It is the type of `CommandEventArgs.EventType`.

## Enum: `CommandEventType`

**Signature**

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,
    Enqueued,
    Dequeued,
    Started,
    Completed,
    Failed,
    Canceled,
    Exited
}
```

##### Fields

| Name | Value | Description |
| --- | --- | --- |
| `None` | `0` | Unset / default. Never raised by a command. |
| `Created` | `1` | A request was accepted. |
| `Enqueued` | `2` | The concurrency cap was reached; the execution waits in the pending queue. |
| `Dequeued` | `3` | The queued execution left the queue and is about to run. |
| `Started` | `4` | The command method started. |
| `Completed` | `5` | The command method returned successfully. |
| `Failed` | `6` | The command method threw a non-cancellation exception. |
| `Canceled` | `7` | The execution was cancelled, or refused by a lock. |
| `Exited` | `8` | The lifecycle ended; the execution left the active set. |

## Sequences

An execution that runs immediately reports `Created`, `Started`, `Completed` and `Exited`. One that had to wait reports `Enqueued` and `Dequeued` around that sequence. A refused call reports `Created` then `Canceled` and never reaches `Exited`; a body that throws reports `Failed` instead of `Completed`.

A stage can have more than one potential emitter. `Canceled` in particular can come from `Interrupt`, from `Clear`, or from the body's own `OperationCanceledException`; `TryMarkCancelReported()` guarantees at most one `Canceled` per execution reaches a handler.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);
var recorder = new CommandEventRecorder(command);

await command.ExecuteAsync(null);
await recorder.FirstExit;

CollectionAssert.AreEqual(
    new[] { CommandEventType.Created, CommandEventType.Started, CommandEventType.Completed, CommandEventType.Exited },
    recorder.Types);
```

## Notes

- **No member corresponds to `CommandOutcome.Refused`.** A refused execution reports `Canceled` and never reaches `Exited`, so this enum alone cannot distinguish a refusal from a cancellation. `ExecuteAndWaitAsync` is the only way to observe a refusal.
- `None = 0` lets a default-initialized value be distinguished from every real stage.
- `Exited` is not a success signal: `CommandEventArgs.Exception` is populated on `Failed` only and stays `null` on `Exited`.
