# MVVM — `VeloxCommand` 生命周期控制

锁定 / 中断 / 清空 / 继续这一族，每个都有同步（fire-and-forget）与可等待的 `Async` 版本。它们也都声明在 `IVeloxCommand` 上，因此生成的命令属性同样暴露它们。

###### `VeloxCommand.Lock` / `VeloxCommand.LockAsync`

**Signature:**
`void Lock()` — `Task LockAsync()`

**返回：** `Task`（异步形态）—— 强制锁设置完成且 `CanExecuteChanged` 已触发后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandControlTests.cs
await command.LockAsync();
Assert.IsFalse(command.CanExecute(null));

await command.ExecuteAsync(null);

Assert.HasCount(1, recorder.Of(CommandEventType.Canceled));
Assert.HasCount(0, recorder.Of(CommandEventType.Started));
```

**说明：** 进入锁会拒绝新调用（`Created` → `Canceled`），但不中断正在运行的调用。`Interrupt` 与 `Clear` 会借用锁再归还，因此原本已锁定的命令之后仍锁定。

###### `VeloxCommand.Unlock` / `VeloxCommand.UnlockAsync`

**Signature:**
`void Unlock()` — `Task UnlockAsync()`

**返回：** `Task`（异步形态）—— 解除锁并尽可能排空队列后完成。

**说明：** 拼写是 `Unlock`，不是 `UnLock`。`IVeloxCommand` 与所有命令类型上都只有这一种拼写。

###### `VeloxCommand.Interrupt` / `VeloxCommand.InterruptAsync`

**Signature:**
`void Interrupt()` — `Task InterruptAsync()`

**返回：** `Task`（异步形态）—— 活动执行被取消后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var running = command.ExecuteAndWaitAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await running.WaitAsync(CommandTestKit.Timeout)).Outcome);
```

**说明：** 取消每个活动项的取消源，并每次执行只触发一条 `Canceled`。排队项留在队列中 —— 用 `Clear` 丢弃它们。已经结束并释放源的项会被跳过（捕获 `ObjectDisposedException`），抛异常的取消回调会被吞掉，使命令不会永久锁定。

###### `VeloxCommand.Clear` / `VeloxCommand.ClearAsync`

**Signature:**
`void Clear()` — `Task ClearAsync()`

**返回：** `Task`（异步形态）—— 队列清空且活动执行被取消后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

var queued = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.PendingCount() == 1);

await command.ClearAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await queued.WaitAsync(CommandTestKit.Timeout)).Outcome);
```

**说明：** 排队项按队列顺序报告 —— 先逐个 `Dequeued`，再 `Canceled`。被丢弃的排队项永远不会运行、不会触发 `Started` / `Exited`，其取消源由 `ClearAsync` 自己释放。

###### `VeloxCommand.Continue` / `VeloxCommand.ContinueAsync`

**Signature:**
`void Continue()` — `Task ContinueAsync()`

**返回：** `Task`（异步形态）。

**说明：** 命令未强制锁定时启动排队工作；否则为空操作。

###### `VeloxCommand.ChangeSemaphore` / `VeloxCommand.ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int s)` — `Task ChangeSemaphoreAsync(int semaphore)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `s` / `semaphore` | `int` | 新的最大并发执行数。 |

**返回：** `Task`（异步形态）。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentOutOfRangeException` | 值小于 1。同步重载在派发前先校验，因为只在 async 方法内抛出的异常会变成未观察异常。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs
await command.ChangeSemaphoreAsync(3);
await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount);
```

**说明：** 提高容量会立即排空队列；降低容量不会取消已在运行的项。
