# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the payload carried by every command lifecycle event and by the internal pending/active queues.

**Signature**

```csharp
public sealed class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;
    public CancellationTokenSource? Cts { get; internal set; } = cts;

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null)
        => new(Parameter, newType, ex ?? Exception, Cts);
}
```

| Member | Meaning |
|---|---|
| `Parameter` | The `object?` argument passed to `Execute` / `ExecuteAsync`. |
| `Exception` | For `Failed`, the exception thrown by the command method; otherwise `null`. |
| `EventType` | The current lifecycle state (`CommandEventType`, see [04_CommandEventType](../04_CommandEventType/index.md)). |
| `Cts` | Per-execution `CancellationTokenSource`. `internal set`: populated by `VeloxCommand` for cancellable commands, read by subscribers and by the control methods. |
| `With(CommandEventType newType, Exception? ex = null)` | Returns a new instance that reuses `Parameter` and `Cts`; when `ex` is `null`, the previous `Exception` is carried over. Used by `VeloxCommand` to re-raise the same execution under a new `EventType`. |

**Notes:**

- `VeloxCommand` is the only producer; consumers subscribe through the `IVeloxCommand` lifecycle events (see [02_IVeloxCommand](../02_IVeloxCommand/index.md)) and read these properties.
- The same physical execution is described by several `CommandEventArgs` instances over its lifetime, from `Created` through to `Exited`, each produced by `With`.
