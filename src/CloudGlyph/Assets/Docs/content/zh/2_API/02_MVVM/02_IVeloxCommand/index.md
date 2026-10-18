# MVVM — `IVeloxCommand`

`VeloxDev.MVVM.IVeloxCommand`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`）是命令契约。它在 `System.Windows.Input.ICommand` 之上增加异步执行、每次执行的生命周期，以及运行期的锁定 / 中断 / 队列控制。具体实现是 `VeloxCommand` 与强类型 arity 族（见 `05_VeloxCommand` 与 `16_强类型命令`）。

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

**未在此声明：** `ExecuteAndWaitAsync`（`IVeloxCommandCompletion`）、`ExecuteAsync(object?, CancellationToken)` / `Execute(object?, out object?)`（`IVeloxCommandResult`）、`IsBusy` / `ActiveCount` / `PendingCount`（`IVeloxCommandStatus`）。把它们加进 `IVeloxCommand` 会破坏所有手写实现者。

##### Events

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `Created` | `CommandEventHandler?` | 执行请求被受理时触发。 |
| `Enqueued` | `CommandEventHandler?` | 并发耗尽、请求加入待处理队列时触发。 |
| `Dequeued` | `CommandEventHandler?` | 排队项离开队列、即将运行时触发。 |
| `Started` | `CommandEventHandler?` | 调用命令方法前触发。 |
| `Completed` | `CommandEventHandler?` | 命令方法成功返回时触发。 |
| `Failed` | `CommandEventHandler?` | 方法体抛出非取消异常时触发；`e.Exception` 携带它。 |
| `Canceled` | `CommandEventHandler?` | 执行被取消或被拒绝时触发。每次执行最多一次。 |
| `Exited` | `CommandEventHandler?` | 执行离开活动集合时触发。被拒绝或被清空的调用不会触发。 |
| `CanExecuteChanged` | `EventHandler?` | 继承自 `ICommand`。 |

##### Methods

###### `IVeloxCommand.ExecuteAsync`

**Signature:**
`Task ExecuteAsync(object? parameter)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `parameter` | `object?` | 传给方法体的实参。 |

**返回：** `Task` —— 在调用被**受理**（启动或入队）时完成，而不是方法体结束时。

**异常：** 接口未声明。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs
private static async Task RunToCompletionAsync(IVeloxCommand command, object? parameter = null)
{
    var exited = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
    command.Exited += _ => exited.TrySetResult(true);
    await command.ExecuteAsync(parameter);
    await exited.Task.WaitAsync(CommandTestKit.Timeout);
}
```

**说明：** 要处理结果，订阅 `Completed` / `Failed` / `Exited`，或使用 `ExecuteAndWaitAsync`。

###### `IVeloxCommand.Lock` / `LockAsync`

**Signature:**
`void Lock()` — `Task LockAsync()`

**返回：** `Task`（异步形态）—— 强制锁设置完成并触发 `CanExecuteChanged` 后完成。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs
private void FreeCommand()
{
    MinusCommand.Lock();
    MinusCommand.Interrupt();
    MinusCommand.Clear();
    MinusCommand.Unlock();
}
```

**说明：** 锁定时 `CanExecute` 返回 `false`，新请求被拒绝（先 `Created` 后 `Canceled`）。运行中的工作不受影响。原本已锁定的命令在 `Interrupt` / `Clear` 之后仍保持锁定。

###### `IVeloxCommand.Unlock` / `UnlockAsync`

**Signature:**
`void Unlock()` — `Task UnlockAsync()`

**返回：** `Task`（异步形态）—— 解除锁并尽可能排空队列后完成。

**说明：** 拼写是 `Unlock`。它声明在接口上，因此生成的命令属性也会暴露它。

###### `IVeloxCommand.Notify`

**Signature:**
`void Notify()`

**返回：** `void` —— 触发 `CanExecuteChanged`。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify();
}
```

**说明：** 每当 `CanExecute{Name}Command` 谓词的结果可能变化时调用。抛异常的 `CanExecuteChanged` 订阅者会被吞掉并通过 `VeloxCommand.HandlerException` 上报。

###### `IVeloxCommand.Interrupt` / `InterruptAsync`

**Signature:**
`void Interrupt()` — `Task InterruptAsync()`

**返回：** `Task`（异步形态）—— 活动执行被取消、命令恢复到此前的锁定状态后完成。

**说明：** 取消正在运行的执行并为每个触发 `Canceled`。排队项保持排队。原本未锁定的命令之后会解锁；原本已锁定的保持锁定。

###### `IVeloxCommand.Clear` / `ClearAsync`

**Signature:**
`void Clear()` — `Task ClearAsync()`

**返回：** `Task`（异步形态）—— 队列清空且活动执行被取消后完成。

**说明：** 先为每个排队项触发 `Dequeued`，再为排队项与活动项触发 `Canceled`。被丢弃的排队项永不到达 `Started` / `Exited`。

###### `IVeloxCommand.Continue` / `ContinueAsync`

**Signature:**
`void Continue()` — `Task ContinueAsync()`

**返回：** `Task`（异步形态）。

**说明：** 命令未强制锁定时启动排队工作；否则为空操作。

###### `IVeloxCommand.ChangeSemaphore` / `ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int semaphore)` — `Task ChangeSemaphoreAsync(int semaphore)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `semaphore` | `int` | 新的最大并发执行数。 |

**返回：** `Task`（异步形态）。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentOutOfRangeException` | `semaphore` 小于 1。同步形态在派发前先校验，避免失败变成未观察异常。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs
await command.ChangeSemaphoreAsync(3);
await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount);
```

**说明：** 提高容量会立即排空队列；降低容量不会取消已在运行的项。
