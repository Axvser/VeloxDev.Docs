# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType`（`Src/Core/VeloxDev.Core/MVVM/CommandEventType.cs`）枚举一次命令执行的生命周期阶段。它是 `CommandEventArgs.EventType` 的类型。

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

| 名称 | 值 | 说明 |
| --- | --- | --- |
| `None` | `0` | 未设置 / 默认。命令从不触发它。 |
| `Created` | `1` | 请求被受理。 |
| `Enqueued` | `2` | 并发容量已满；执行在待处理队列中等待。 |
| `Dequeued` | `3` | 排队执行离开队列，即将运行。 |
| `Started` | `4` | 命令方法开始。 |
| `Completed` | `5` | 命令方法成功返回。 |
| `Failed` | `6` | 命令方法抛出非取消异常。 |
| `Canceled` | `7` | 执行被取消，或因锁被拒绝。 |
| `Exited` | `8` | 生命周期结束；执行离开活动集合。 |

## 序列

立即运行的一次执行报告 `Created`、`Started`、`Completed` 与 `Exited`。需要等待的执行在这组序列前后加上 `Enqueued` 与 `Dequeued`。被拒绝的调用报告 `Created` 后直接 `Canceled`，永不到达 `Exited`；方法体抛异常时报告 `Failed` 而非 `Completed`。

同一阶段可能有多个潜在发射者。`Canceled` 尤其可能来自 `Interrupt`、`Clear` 或方法体自己的 `OperationCanceledException`；`TryMarkCancelReported()` 保证每次执行最多只有一条 `Canceled` 到达处理器。

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

## 说明

- **没有成员对应 `CommandOutcome.Refused`。** 被拒绝的执行报告 `Canceled` 且永不到达 `Exited`，因此仅凭该枚举无法区分拒绝与取消。只有 `ExecuteAndWaitAsync` 能观察拒绝。
- `None = 0` 让默认初始化值可与任何真实阶段区分。
- `Exited` 不是成功信号：`CommandEventArgs.Exception` 只在 `Failed` 上填充，在 `Exited` 上保持 `null`。
