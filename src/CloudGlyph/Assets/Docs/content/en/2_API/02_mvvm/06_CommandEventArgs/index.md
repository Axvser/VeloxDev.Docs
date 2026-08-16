# MVVM — `CommandEventArgs`

**Signature** (`VeloxCommand.cs`, lines 382-394):

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

- **Notes:** `Cts` is `internal set` — it is populated by `VeloxCommand` for cancellable commands. `With` produces a new instance carrying the same parameter/token, used to re-raise the same invocation under a different `EventType`.
