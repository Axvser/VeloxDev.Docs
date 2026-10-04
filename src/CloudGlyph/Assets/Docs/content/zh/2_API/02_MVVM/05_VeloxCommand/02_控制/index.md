# MVVM — `VeloxCommand` 生命周期控制

加锁 / 中断 / 清空 / 继续这一族，每个都有同步（即发即忘）版与可等待的 `Async` 孪生版。它们都同时声明在 `IVeloxCommand` 上，因此生成的命令属性也暴露这些方法。

###### `VeloxCommand.Lock` / `VeloxCommand.LockAsync`

**Signature:**
`void Lock()` —— `Task LockAsync()`

**Returns:** `Task`（异步版）—— 强制锁设置完成、且 `Notify()` 已执行后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandControlTests.cs, lines 24-31
await command.LockAsync();
Assert.IsFalse(command.CanExecute(null), "a locked command reports itself as not executable");

await command.ExecuteAsync(null);

Assert.HasCount(1, recorder.Of(CommandEventType.Canceled), "a call arriving at a locked command is refused");
Assert.HasCount(0, recorder.Of(CommandEventType.Started), "refused means never started");
```

**Notes:** 进入锁定会拒绝新调用（`Created` → `Canceled`），但不中断正在运行的调用。`Interrupt` 与 `Clear` 会借用锁再归还，因此本就锁定的命令事后保持锁定。

###### `VeloxCommand.Unlock` / `VeloxCommand.UnlockAsync`

**Signature:**
`void Unlock()` —— `Task UnlockAsync()`

**Returns:** `Task`（异步版）—— 锁被清除、并在容量允许范围内排空队列后完成。

**Notes:** 拼写是 `Unlock` —— 接口早期版本用的是 `UnLock`。`IVeloxCommand` 与 `VeloxCommand` 上现在都只有当前拼写。

###### `VeloxCommand.Interrupt` / `VeloxCommand.InterruptAsync`

**Signature:**
`void Interrupt()` —— `Task InterruptAsync()`

**Returns:** `Task`（异步版）—— 活动执行被取消后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 58-70
var running = command.ExecuteAndWaitAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await running.WaitAsync(CommandTestKit.Timeout)).Outcome);
```

**Notes:** 取消每个活动项的 `CancellationTokenSource`，并为每次执行触发一次 `Canceled`。排队项留在队列里 —— 要丢弃它们请用 `Clear`。已经跑完并释放过源的方法体会被跳过（`ObjectDisposedException` 被捕获），取消回调抛出的异常也会被吞掉，因此命令绝不会被永久锁死。

###### `VeloxCommand.Clear` / `VeloxCommand.ClearAsync`

**Signature:**
`void Clear()` —— `Task ClearAsync()`

**Returns:** `Task`（异步版）—— 队列清空、活动执行被取消后完成。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 84-100
_ = command.ExecuteAsync(null);                       // takes the slot
await gate.WaitForStartedAsync();

var queued = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.PendingCount() == 1);

await command.ClearAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await queued.WaitAsync(CommandTestKit.Timeout)).Outcome,
    "a queued call dropped by Clear never raises Exited either");
```

**Notes:** 排队项按队列顺序上报 —— 先逐个 `Dequeued`，再 `Canceled`。被丢弃的排队项从不运行、从不触发 `Started` / `Exited`，而它的每次执行 `CancellationTokenSource` 由 `ClearAsync` 自己释放（没有别人会做）。

###### `VeloxCommand.Continue` / `VeloxCommand.ContinueAsync`

**Signature:**
`void Continue()` —— `Task ContinueAsync()`

**Returns:** `Task`（异步版）。

**Notes:** 命令未处于强制锁定时启动排队中的工作；否则为空操作。一次什么都没留下的 `Clear` 之后再 `Continue`，不会启动任何东西。

###### `VeloxCommand.ChangeSemaphore` / `VeloxCommand.ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int s)` —— `Task ChangeSemaphoreAsync(int semaphore)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `s` / `semaphore` | `int` | 新的最大并发执行数。 |

**Returns:** `Task`（异步版）。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `ArgumentOutOfRangeException` | 取值小于 1。同步重载在派发**之前**校验，因为只在 async 方法内部抛出的异常会变成未被观察的异常而被静默丢弃。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs, lines 119-122
await command.ChangeSemaphoreAsync(3);

await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount, "raising the cap is what releases the queue - nothing else will");
```

**Notes:** 调高容量会立即排空队列；调低容量绝不会取消任何已在运行的任务。

## 源码引用

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` —— `LockAsync` 601、`UnlockAsync` 625、`InterruptAsync` 642、`ClearAsync` 686、`ContinueAsync` 750、`ChangeSemaphoreAsync` 774、`TryStartPendingAsync` 794。
