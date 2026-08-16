# MVVM — `IVeloxCommand`

由 `VeloxCommand` 实现的运行时契约。

**签名**（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`，第 5-31 行）：

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

继承自 `ICommand`：`bool CanExecute(object?)`、`void Execute(object?)`、事件 `EventHandler CanExecuteChanged`。

**生命周期事件** — 负载为单个 `CommandEventArgs`：

| 事件 | 触发时机 |
|---|---|
| `Created` | `ExecuteAsync` 为本次触发创建 `CommandEventArgs` |
| `Enqueued` | 容量耗尽，条目加入 `_pendingQueue` |
| `Dequeued` | 排队的条目移入活动列表 |
| `Started` | 即将调用命令方法 |
| `Completed` | 命令方法成功返回 |
| `Failed` | 命令方法抛出异常（非取消） |
| `Canceled` | 调用被取消（强制锁、`Interrupt`、`Clear` 或 `OperationCanceledException`） |
| `Exited` | 调用结束并从活动列表移除 |

**控制方法：**

| 方法 | 用途 |
|---|---|
| `ExecuteAsync(object?)` | 入队/开始执行；返回的 `Task` 在调用被分派后完成（而非完成后）。 |
| `Lock()` / `UnLock()` | 切换强制锁定；锁定时新触发会被取消，正在执行的命令不会被打断。 |
| `Interrupt()` / `InterruptAsync()` | 取消当前活动的调用。 |
| `Clear()` / `ClearAsync()` | 取消活动 + 所有排队的调用。 |
| `Continue()` / `ContinueAsync()` | 排空待处理队列（例如 `UnLock` 之后）。 |
| `ChangeSemaphore(int)` | 运行时调整最大并发数（`< 1` 时忽略）。 |
| `Notify()` | 触发 `CanExecuteChanged`。 |

- **示例：** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 157-180 行 — `FreeCommand` / `FreeCommandAsync` 调用 `Lock`、`Interrupt`、`Clear`、`UnLock`（以及 `await` 版本）。
