# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler` (`Src/Core/VeloxDev.Core/MVVM/CommandEventArgs.cs`) is the delegate type of every lifecycle event on `IVeloxCommand`. Its generic twin carries the typed payload.

## Delegates

**Signatures**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);

public delegate void CommandEventHandler<TParam, TResult>(CommandEventArgs<TParam, TResult> e);
```

| Parameter | Type | Description |
| --- | --- | --- |
| `e` | `CommandEventArgs` / `CommandEventArgs<TParam, TResult>` | One stage of one execution. |

**Returns:** `void`.

**Exceptions:** none declared. A handler that throws is caught by the pipeline, reported through the static `HandlerException` event, and does not disturb the command.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandTestKit.cs
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

- The payload is a single `CommandEventArgs`, not a conventional `(object? sender, EventArgs e)` pair; a handler has no `sender` and must close over the command if it needs it.
- `IVeloxCommand` declares one non-generic event of this type per lifecycle stage.
- `IVeloxCommandEvents<TParam, TResult>` declares the typed counterpart. Because a class cannot declare two public events with the same name, the typed events are implemented explicitly; subscribe through a reference typed as `IVeloxCommandEvents<TParam, TResult>`.
- A subscriber that throws does not disturb the command. The exception is caught, reported through `VeloxCommand.HandlerException` if anyone is subscribed, and otherwise discarded. `CanExecuteChanged` handlers behave the same way.
- A single `using VeloxDev.MVVM;` is enough to write a handler as a lambda: `cmd.Completed += e => { ... };`.
