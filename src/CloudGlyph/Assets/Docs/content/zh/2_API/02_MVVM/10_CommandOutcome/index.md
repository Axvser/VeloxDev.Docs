# MVVM — `CommandOutcome`

`VeloxDev.MVVM.CommandOutcome`（`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`）说明单次执行如何结束。它是 `CommandCompletion.Outcome` 的类型。

## Enum: `CommandOutcome`

**Signature**

```csharp
public enum CommandOutcome
{
    /// <summary>The body ran to completion without throwing.</summary>
    Completed,

    /// <summary>The body threw.</summary>
    Failed,

    /// <summary>The execution was cancelled.</summary>
    Canceled,

    /// <summary>The call never ran because the command was locked.</summary>
    Refused,
}
```

##### Fields

| 名称 | 值 | 说明 |
|---|---|---|
| `Completed` | `0` | 方法体跑完且未抛异常。 |
| `Failed` | `1` | 方法体抛了异常。`CommandCompletion.Exception` 携带该失败。 |
| `Canceled` | `2` | 执行被取消 —— 由 `Interrupt` 或 `Clear` 这类生命周期调用、由方法体遵守 token、或因为它仍在排队时 `Clear` 清空了队列。 |
| `Refused` | `3` | 因命令被锁定而从未运行。 |

**关于取值：** 声明中未显式赋值，因此成员按声明顺序取 `0, 1, 2, 3`。`Completed == default`，这意味着默认初始化的 `CommandCompletion` 读起来是一次成功且 `Exception == null`。

## 为什么 `Canceled` 覆盖两种情形

被 `Clear` 从队列丢弃的调用上报为 `Canceled` 而不是单独的结局，因为从调用方视角看答案是一样的：它永远不会运行。

## 为什么 `Refused` 没有事件对应物

`Refused` 刻意**没有**对应的 `CommandEventType` 成员。被拒绝的调用上报 `CommandEventType.Canceled`，且永远到不了 `CommandEventType.Exited`，因此单看 `CommandEventType` 无法把拒绝与取消区分开。所以 `CommandOutcome.Refused` **只能**通过 `ExecuteAndWaitAsync` 观察。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 72-82
var command = new VeloxCommand(() => Task.CompletedTask);
await command.LockAsync();

var completion = await command.ExecuteAndWaitAsync(null).WaitAsync(CommandTestKit.Timeout);

Assert.AreEqual(CommandOutcome.Refused, completion.Outcome,
    "a refused call never raises Exited, so this is the only way to observe it");
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 84-100
var queued = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.PendingCount() == 1);

await command.ClearAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await queued.WaitAsync(CommandTestKit.Timeout)).Outcome,
    "a queued call dropped by Clear never raises Exited either");
```
