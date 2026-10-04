# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）枚举单次命令执行的生命周期状态。它是 `CommandEventArgs.EventType` 的类型。

## Enum: `CommandEventType`

**Signature**

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,   // Created
    Enqueued,  // Enqueued, waiting to run
    Dequeued,  // Dequeued, ready to execute
    Started,   // Execution actually started
    Completed, // Executed successfully
    Failed,    // Execution failed
    Canceled,  // Cancelled
    Exited     // Lifecycle ended
}
```

##### Fields

| 名称 | 值 | 说明 |
|---|---|---|
| `None` | `0` | 未设置 / 默认值。`VeloxCommand` 从不触发它。 |
| `Created` | `1` | 请求被受理且其负载已分配。 |
| `Enqueued` | `2` | 并发容量已达上限；执行在等待队列中。 |
| `Dequeued` | `3` | 排队执行离开队列，即将运行。 |
| `Started` | `4` | 命令方法真正开始执行。 |
| `Completed` | `5` | 命令方法成功返回。 |
| `Failed` | `6` | 命令方法抛出非取消异常。 |
| `Canceled` | `7` | 执行被取消，或被锁拒绝。 |
| `Exited` | `8` | 生命周期结束；执行离开活动集合。 |

## 时序

立即执行的执行会触发 `Created`、`Started`、`Completed`、`Exited`。需要等待空闲槽位的会在同一串前后多出 `Enqueued` 与 `Dequeued`。被锁拒绝或被中断的会以 `Canceled` 取代 `Completed`；方法体抛异常的会触发 `Failed`。

一个阶段可能有多个发出者，因此同一次执行可能出现两次相同的值：`Canceled` 既由 `Interrupt` 与 `Clear` 触发，也由方法体自身的 `OperationCanceledException` 触发。`RaiseCanceled` 用 `TryMarkCancelReported()` 守住这一点，因此每次执行至多有一条 `Canceled` 到达处理器。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs, lines 44-56
var command = new VeloxCommand(() => Task.CompletedTask);
var recorder = new CommandEventRecorder(command);

await command.ExecuteAsync(null);
await recorder.FirstExit;

CollectionAssert.AreEqual(
    new[] { CommandEventType.Created, CommandEventType.Started, CommandEventType.Completed, CommandEventType.Exited },
    recorder.Types);
```

## Notes

- **没有任何成员对应 `CommandOutcome.Refused`。** 被拒绝的执行上报的是 `Canceled`，且永远到不了 `Exited`，因此单看本枚举无法把“被拒绝”与“被取消”区分开。`ExecuteAndWaitAsync` 是观察拒绝的唯一途径。详见 `10_CommandOutcome` 页。
- `None = 0` 的存在是为了让默认初始化的值能与任何真实阶段区分开。
- `Exited` 不是成功信号：`CommandEventArgs.Exception` 只在 `Failed` 上有值，在 `Exited` 上仍为 `null`。
