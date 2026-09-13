# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是 `IVeloxCommand` 的密封具体实现（见 [IVeloxCommand](../02_IVeloxCommand/index.md)）。

**主构造函数**

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

**便捷构造函数与静态工厂**

| 成员 | 签名 |
|---|---|
| `VeloxCommand` | `(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — 包装 `await command()`；没有逐次执行的取消令牌。 |
| `VeloxCommand` | `(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — 同步、带参。 |
| `VeloxCommand` | `(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)` — 同步、无参。 |
| `CreateTaskOnlyWithParameter` | `static VeloxCommand(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — `await command(parameter)`；没有逐次执行的取消令牌。 |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — `await command(ct)`；每次执行会创建一个令牌。 |

**异常：** 当主构造函数的 `command` 委托为 `null` 时抛出 `ArgumentNullException`（参数名 `command`；`_command = command ?? throw new ArgumentNullException(nameof(command));`）。测试：`VeloxCommandTests.Constructor_NullCommand_Throws`（`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`）。

**取消说明：** 只有主构造函数与 `CreateTaskOnlyWithCancellationToken` 会为每次执行创建 `CancellationTokenSource`（`_isCtsNeeded = true`）。其余入口使用框架的默认（永不被取消）令牌运行，因此 `Lock` / `Interrupt` / `Clear` 无法中断底层方法，不过这些调用的终态 `Canceled` 事件仍会被触发。

## 成员

实现 `IVeloxCommand` 的全部事件：`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`，外加 `ICommand.CanExecuteChanged`。方法：

| 方法 | 行为 |
|---|---|
| `bool CanExecute(object? parameter)` | `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked`。 |
| `void Execute(object? parameter)` | 即发即弃派发：`_ = ExecuteAsync(parameter);`。 |
| `Task ExecuteAsync(object? parameter)` | 分配 `CommandEventArgs(parameter, Created)`（可取消时附带 CTS），触发 `Created`，然后在低于并发上限时立即运行（触发 `Started` → 终态事件 → `Exited`），否则入队（触发 `Enqueued`；派发时再触发 `Dequeued`）。返回在条目派发后完成，而非命令结束时。 |
| `void Notify()` | 触发 `CanExecuteChanged`（订阅者异常被吞掉）。 |
| `void Lock()` / `Task LockAsync()` | 设置强制锁；后续触发被取消，正在执行的调用继续。 |
| `void UnLock()` / `Task UnLockAsync()` | 清除强制锁并排空待处理队列。 |
| `void Interrupt()` / `Task InterruptAsync()` | 强制锁、快照并清空活动列表、逐个取消活动条目（触发 `Canceled`），然后解锁。 |
| `void Clear()` / `Task ClearAsync()` | 强制锁、快照活动列表并把所有待处理条目出队（每个触发 `Dequeued`）、全部取消（触发 `Canceled`），然后解锁。 |
| `void Continue()` / `Task ContinueAsync()` | 除非处于强制锁定，否则排空待处理队列。 |
| `void ChangeSemaphore(int)` / `Task ChangeSemaphoreAsync(int)` | 更新 `_maxConcurrency`（`< 1` 被忽略）并排空。 |

内部用 `SemaphoreSlim` 同步执行；事件触发（`RaiseCommandEvent`）与 `CanExecuteChanged` 都是异常安全的。

## 在生成代码中的用法

Command 生成器会生成一个懒初始化属性来调用这些构造函数/工厂。`canValidate: true` 形态（`CommandWriter.cs` 模板，应用于 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs` 的 `Minus`）：

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_MinusCommand = null;
public VeloxDev.MVVM.IVeloxCommand MinusCommand
{
    get
    {
        _buffer_MinusCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Minus,
            canExecute: CanExecuteMinusCommand,
            semaphore: 1);
        return _buffer_MinusCommand;
    }
}
private partial bool CanExecuteMinusCommand(object? parameter);
```

直接构造的覆盖见 `Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`（`Execute_SyncAction_Completes`、`Execute_ActionWithParameter_ReceivesParameter`、`Execute_AsyncFunc_Completes`、`CanExecute_NoPredicate_ReturnsTrue`、`CanExecute_WithPredicate_RespectsIt`、`Constructor_NullCommand_Throws`、`CreateTaskOnlyWithParameter_Works`）。
