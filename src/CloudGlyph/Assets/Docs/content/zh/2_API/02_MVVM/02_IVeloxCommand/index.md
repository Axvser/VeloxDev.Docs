# MVVM — `IVeloxCommand`

`VeloxDev.MVVM.IVeloxCommand`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`）是命令契约。它继承 `System.Windows.Input.ICommand`，加入异步执行模型、每次执行的生命周期，以及运行时的锁 / 中断 / 队列控制。具体实现是 `VeloxCommand`（见 [VeloxCommand](../03_VeloxCommand/index.md)）。

**签名**

```csharp
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
    public void UnLock();
    public void Notify();
    public void Clear();
    public void Interrupt();
    public void Continue();
    public void ChangeSemaphore(int semaphore);

    public Task ExecuteAsync(object? parameter);
    public Task LockAsync();
    public Task UnLockAsync();
    public Task ClearAsync();
    public Task InterruptAsync();
    public Task ContinueAsync();
    public Task ChangeSemaphoreAsync(int semaphore);
}
```

**继承自 `ICommand`：** `bool CanExecute(object? parameter)`、`void Execute(object? parameter)`、事件 `EventHandler? CanExecuteChanged`。

## 生命周期事件

每个生命周期事件都携带描述一次执行的单个 `CommandEventArgs`（见 [CommandEventArgs](../06_CommandEventArgs/index.md)）。正常流程下，一次 `Created` 调用要么立即运行（`Started`），要么在队列中等待（`Enqueued`），随后经过 `Dequeued` → `Started` 到达终态（`Completed`、`Failed` 或 `Canceled`），最后由 `Exited` 收尾。若调用在真正开始前就被取消（处于强制锁定，或仍排着队时执行了 `Clear`），则直接触发 `Canceled`，没有 `Started` / `Exited`。

| 事件 | 触发时机 |
|---|---|
| `Created` | `ExecuteAsync` 为该触发分配负载 |
| `Enqueued` | 容量耗尽，条目加入待处理队列 |
| `Dequeued` | 排队的条目移入活动列表 |
| `Started` | 即将调用命令方法 |
| `Completed` | 命令方法成功返回 |
| `Failed` | 命令方法抛出非取消异常 |
| `Canceled` | 调用被取消（强制锁、`Interrupt`、`Clear` 或 `OperationCanceledException`） |
| `Exited` | 调用结束并从活动列表移除 |

## 控制方法

| 方法 | 用途 |
|---|---|
| `ExecuteAsync(object?)` | 派发一次执行：低于并发上限则立即运行，否则入队。返回的 `Task` 在条目被派发后完成，而非命令方法结束时。 |
| `Lock()` / `LockAsync()` | 进入强制锁定状态：新的触发会被取消，正在运行的命令继续运行。 |
| `UnLock()` / `UnLockAsync()` | 退出强制锁定状态并排空待处理队列。 |
| `Interrupt()` / `InterruptAsync()` | 取消当前活动的调用。 |
| `Clear()` / `ClearAsync()` | 取消当前活动的调用以及所有排队的调用。 |
| `Continue()` / `ContinueAsync()` | 排空待处理队列（强制锁定时为无操作）。 |
| `ChangeSemaphore(int)` / `ChangeSemaphoreAsync(int)` | 运行时调整最大并发上限（`< 1` 被忽略）。 |
| `Notify()` | 触发 `CanExecuteChanged`。 |

同步控制方法是即发即弃的便捷形式；`Async` 变体才是真正的工作并可 `await`。当注册了谓词（见 [VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md) 的 `canValidate`）时，请在影响 `CanExecute` 的状态变化后调用 `Notify()`。

**示例**（`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 158-179 行）：`FreeCommand` / `FreeCommandAsync` 对 `MinusCommand` 执行 `Lock`、`Interrupt`、`Clear`、`UnLock` 及其 `await` 版本。
