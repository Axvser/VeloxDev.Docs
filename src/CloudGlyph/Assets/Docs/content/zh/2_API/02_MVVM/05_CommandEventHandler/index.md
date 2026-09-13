# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是命令生命周期事件的委托类型。

**签名**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

**备注：**

- 负载是单个 `CommandEventArgs`，不是标准 .NET 的 `(object? sender, CommandEventArgs e)` 二元组。
- `IVeloxCommand` 为每个生命周期状态各暴露一个该类型的事件（`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`）——见 [IVeloxCommand](../02_IVeloxCommand/index.md)。
- `VeloxCommand` 会吞掉订阅者异常（`RaiseCommandEvent`），因此单个出错的处理器不会中断命令管线。
