# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是每个命令生命周期事件以及内部待处理/活动队列所携带的负载。

**签名**

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

| 成员 | 含义 |
|---|---|
| `Parameter` | 传给 `Execute` / `ExecuteAsync` 的 `object?` 参数。 |
| `Exception` | `Failed` 时是命令方法抛出的异常；其余为 `null`。 |
| `EventType` | 当前生命周期状态（`CommandEventType`，见 [CommandEventType](../04_CommandEventType/index.md)）。 |
| `Cts` | 每次执行的 `CancellationTokenSource`。`internal set`：由 `VeloxCommand` 为可取消命令填充，订阅者与控制方法只读。 |
| `With(CommandEventType newType, Exception? ex = null)` | 返回复用了 `Parameter` 与 `Cts` 的新实例；`ex` 为 `null` 时沿用原 `Exception`。`VeloxCommand` 用它把同一执行以新 `EventType` 重新触发。 |

**备注：**

- 唯一的生产者是 `VeloxCommand`；使用者通过 `IVeloxCommand` 生命周期事件订阅（见 [IVeloxCommand](../02_IVeloxCommand/index.md)）并读取这些属性。
- 同一物理执行在其生命周期中由多个 `CommandEventArgs` 实例描述（从 `Created` 直至 `Exited`），每个都由 `With` 产生。
