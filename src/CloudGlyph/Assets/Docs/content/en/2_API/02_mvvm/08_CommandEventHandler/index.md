# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the delegate type of every lifecycle event on `IVeloxCommand`.

## Delegate: `CommandEventHandler`

**Signature**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

| Parameter | Type | Description |
|---|---|---|
| `e` | `CommandEventArgs` | One stage of one execution. |

**Returns:** `void`.

**Exceptions:** none declared. A handler that throws propagates only as far as `VeloxCommand`'s swallow point, which reports it through `HandlerException` and lets the lifecycle continue.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandTestKit.cs, lines 65-83
internal CommandEventRecorder(IVeloxCommand command)
{
    command.Created += Record;
    command.Enqueued += Record;
    command.Dequeued += Record;
    command.Started += Record;
    command.Completed += Record;
    command.Failed += Record;
    command.Canceled += Record;
    command.Exited += e =>
    {
        Record(e);
        if (Interlocked.Increment(ref _exitCount) == 1)
        {
            _firstExit.TrySetResult(true);
        }
    };
}

private void Record(CommandEventArgs e) => _events.Enqueue(e);
```

## Notes

- The payload is a single `CommandEventArgs`, not the conventional `(object? sender, CommandEventArgs e)` pair — a handler therefore has no `sender`, and must close over the command if it needs it.
- `IVeloxCommand` declares one event of this type per lifecycle stage: `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`. The event name is what identifies the stage for a subscriber; the payload's own `EventType` repeats it.
- A subscriber that throws does not disturb the command: the exception is caught, reported through the static `VeloxCommand.HandlerException` event if anyone is subscribed, and discarded. This holds for `CanExecuteChanged` handlers too.
- Because the delegate is declared in the same namespace as the attributes, a single `using VeloxDev.MVVM;` is enough to write a handler with a lambda: `cmd.Completed += e => { ... };`.
