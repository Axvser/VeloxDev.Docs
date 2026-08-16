# MVVM — `CommandEventHandler`

**签名**（`VeloxCommand.cs`，第 380 行）：

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

- **备注：** 负载是单个 `CommandEventArgs`，不是 `(object sender, CommandEventArgs)` 形式 — 与标准 .NET 事件模式不同。
