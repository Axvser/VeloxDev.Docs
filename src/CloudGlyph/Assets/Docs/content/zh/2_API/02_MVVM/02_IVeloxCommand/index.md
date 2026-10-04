# MVVM — `IVeloxCommand`

`VeloxDev.MVVM.IVeloxCommand`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`）是命令契约。它在 `System.Windows.Input.ICommand` 之上增加了异步执行模型、每次执行的生命周期，以及运行时的锁 / 中断 / 队列控制。具体实现是 `VeloxCommand`（见 `05_VeloxCommand`）。

## Interface: `IVeloxCommand`

**Signature**

```csharp
using System.Windows.Input;

namespace VeloxDev.MVVM
{
    public interface IVeloxCommand : ICommand
    {
        public event CommandEventHandler? Created;
        public event CommandEventHandler? Started;
        public event CommandEventHandler? Completed;
        public event CommandEventHandler? Canceled;
        public event CommandEventHandler? Failed;
        public event CommandEventHandler? Exited;
        public event CommandEventHandler? Enqueued;
        public event CommandEventHandler? Dequeued;

        public void Lock();
        public void Unlock();
        public void Notify();
        public void Clear();
        public void Interrupt();
        public void Continue();
        public void ChangeSemaphore(int semaphore);

        public Task ExecuteAsync(object? parameter);
        public Task LockAsync();
        public Task UnlockAsync();
        public Task ClearAsync();
        public Task InterruptAsync();
        public Task ContinueAsync();
        public Task ChangeSemaphoreAsync(int semaphore);
    }
}
```

**继承自 `ICommand`：** `bool CanExecute(object? parameter)`、`void Execute(object? parameter)`、事件 `EventHandler? CanExecuteChanged`。

**不在此声明：** `ExecuteAndWaitAsync`（在 `IVeloxCommandCompletion` 上）、`IsBusy` / `ActiveCount` / `PendingCount`（在 `IVeloxCommandStatus` 上）。两者都可经 `VeloxCommandExtensions` 从本接口取得 —— 把它们加进 `IVeloxCommand` 会破坏所有手写实现者。

##### Events

| 名称 | 类型 | 说明 |
|---|---|---|
| `Created` | `CommandEventHandler?` | 执行请求被受理时触发。 |
| `Enqueued` | `CommandEventHandler?` | 容量耗尽、请求进入等待队列时触发。 |
| `Dequeued` | `CommandEventHandler?` | 排队项离开队列、即将运行时触发。 |
| `Started` | `CommandEventHandler?` | 命令方法被调用前一刻触发。 |
| `Completed` | `CommandEventHandler?` | 命令方法成功返回时触发。 |
| `Failed` | `CommandEventHandler?` | 命令方法抛出非取消异常时触发；`e.Exception` 携带它。 |
| `Canceled` | `CommandEventHandler?` | 执行被取消或被拒绝时触发。每次执行至多一次。 |
| `Exited` | `CommandEventHandler?` | 执行结束并离开活动集合时触发。被拒绝或被清空的调用不会触发它。 |
| `CanExecuteChanged` | `EventHandler?` | 继承自 `ICommand`。 |

##### Methods

###### `IVeloxCommand.ExecuteAsync`

**Signature:**
`Task ExecuteAsync(object? parameter)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameter` | `object?` | 传给命令方法体的实参。 |

**Returns:** `Task` —— 调用被**受理**（开始或入队）后完成，而非方法体结束时。

**Exceptions:** 接口未声明任何异常。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs, lines 141-147
private static async Task RunToCompletionAsync(IVeloxCommand command, object? parameter = null)
{
    var exited = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
    command.Exited += _ => exited.TrySetResult(true);
    await command.ExecuteAsync(parameter);
    await exited.Task.WaitAsync(CommandTestKit.Timeout);
}
```

**Notes:** 要依据结果行事，请订阅 `Completed` / `Failed` / `Exited`，或使用 `ExecuteAndWaitAsync`。

###### `IVeloxCommand.Lock` / `LockAsync`

**Signature:**
`void Lock()` —— `Task LockAsync()`

**Returns:** `Task`（异步版）—— 强制锁设置完成后完成。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 158-167
private void FreeCommand()
{
    MinusCommand.Lock();   // enter the locked state: prevents new commands from triggering but
                           // does not interrupt the currently running command

    MinusCommand.Interrupt();    // interrupt the current command
    MinusCommand.Clear();        // interrupt the current command and all queued commands

    MinusCommand.Unlock(); // release the lock
}
```

**Notes:** 锁定期间 `CanExecute` 返回 `false`，新请求被拒绝（先触发 `Created` 再触发 `Canceled`）。运行中的工作不受影响。已经锁定的命令在 `Interrupt` / `Clear` 之后仍然锁定。

###### `IVeloxCommand.Unlock` / `UnlockAsync`

**Signature:**
`void Unlock()` —— `Task UnlockAsync()`

**Returns:** `Task`（异步版）—— 锁释放、并在容量允许范围内排空队列后完成。

**Notes:** 成员拼写是 `Unlock`。它声明在接口上，因此 `VeloxCommand` 与生成的命令属性**都**会转发它。

###### `IVeloxCommand.Notify`

**Signature:**
`void Notify()`

**Returns:** `void` —— 触发 `CanExecuteChanged`。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 34-37
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}
```

**Notes:** 每当 `CanExecute{名称}Command` 谓词的结果可能变化时调用它。抛异常的 `CanExecuteChanged` 订阅者会被吞掉，并通过 `VeloxCommand.HandlerException` 上报。

###### `IVeloxCommand.Interrupt` / `InterruptAsync`

**Signature:**
`void Interrupt()` —— `Task InterruptAsync()`

**Returns:** `Task`（异步版）—— 活动中的执行被取消、命令回到此前的锁定状态后完成。

**Notes:** 取消正在运行的执行并为每次触发 `Canceled`。排队项留在队列里。原本未锁定的命令之后会解锁；本就锁定的命令保持锁定。

###### `IVeloxCommand.Clear` / `ClearAsync`

**Signature:**
`void Clear()` —— `Task ClearAsync()`

**Returns:** `Task`（异步版）—— 队列清空且活动执行被取消后完成。

**Notes:** 先为每个排队项触发 `Dequeued`，再为排队项与活动项统一触发 `Canceled`。这样被丢弃的排队项永远到不了 `Started` / `Exited`。

###### `IVeloxCommand.Continue` / `ContinueAsync`

**Signature:**
`void Continue()` —— `Task ContinueAsync()`

**Returns:** `Task`（异步版）。

**Notes:** 命令未处于强制锁定时启动排队中的工作；否则为空操作。一次什么都没留下的 `Clear` 之后再 `Continue`，不会启动任何东西。

###### `IVeloxCommand.ChangeSemaphore` / `ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int semaphore)` —— `Task ChangeSemaphoreAsync(int semaphore)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `semaphore` | `int` | 新的最大并发执行数。 |

**Returns:** `Task`（异步版）。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `ArgumentOutOfRangeException` | `semaphore` 小于 1。同步版在派发前先自行校验，以免该失败变成未被观察的异常而丢失。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs, lines 119-122
await command.ChangeSemaphoreAsync(3);

await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount, "raising the cap is what releases the queue - nothing else will");
```

**Notes:** 调高容量会立即排空队列现在能容纳的部分。
