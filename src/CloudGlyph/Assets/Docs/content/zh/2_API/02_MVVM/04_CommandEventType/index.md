# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）枚举一次命令执行所处的生命周期状态。

**签名**

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

| 值 | 含义 |
|---|---|
| `None = 0` | 未设置 / 默认。 |
| `Created` | 为该触发分配了 `CommandEventArgs`。 |
| `Enqueued` | 达到并发上限；该执行在待处理队列中等待。 |
| `Dequeued` | 排队的执行被取出，即将运行。 |
| `Started` | 命令方法真正开始。 |
| `Completed` | 命令方法成功返回。 |
| `Failed` | 命令方法抛出非取消异常。 |
| `Canceled` | 执行被取消。 |
| `Exited` | 生命周期结束；执行已从活动列表移除。 |

`CommandEventType` 会被打在 `CommandEventArgs` 上（见 [06_CommandEventArgs](../06_CommandEventArgs/index.md)），这正是同一执行由 `VeloxCommand` 在其生命周期中被反复重新触发的方式。该值通过哪个事件送达由 `IVeloxCommand` 定义（见 [02_IVeloxCommand](../02_IVeloxCommand/index.md)）。
