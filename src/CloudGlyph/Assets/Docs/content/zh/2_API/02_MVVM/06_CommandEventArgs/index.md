# MVVM — `CommandEventArgs`

**签名**（`VeloxCommand.cs`，第 382-394 行）：

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

- **备注：** `Cts` 为 `internal set` — 由 `VeloxCommand` 为可取消命令填充。`With` 生成携带相同参数/token 的新实例，用于在同一个调用下以不同 `EventType` 重新触发。
