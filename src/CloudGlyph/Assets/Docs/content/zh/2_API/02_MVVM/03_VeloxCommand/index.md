# MVVM — `VeloxCommand`

`IVeloxCommand` 的密封实现（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）。

**主构造函数**（第 16-18 行）：

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

**静态工厂与便捷构造函数**（第 20-77 行）：

| 成员 | 签名 |
|---|---|
| `CreateTaskOnlyWithParameter` | `static VeloxCommand(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` — 设置 `_isCtsNeeded = false` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task>, ...)` | 包装 `await command()`；设置 `_isCtsNeeded = false` |
| `VeloxCommand(Action<object?>, ...)` | 同步带参；`_isCtsNeeded = false` |
| `VeloxCommand(Action, ...)` | 同步无参；`_isCtsNeeded = false` |

**异常：** 当 `command` 为 `null` 时抛出 `ArgumentNullException`（第 79 行）。**测试：** `VeloxCommandTests.Constructor_NullCommand_Throws`（`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`，第 62-65 行）。

**内部状态**（第 82-90 行）：`SemaphoreSlim _stateLock(1, 1)`、`Queue<CommandEventArgs> _pendingQueue`、`List<CommandEventArgs> _active`、`int _maxConcurrency = Math.Max(1, semaphore)`、`bool _isForceLocked`、`bool _isCtsNeeded = true`、静态 `CancellationToken _defct`。

**行为：**

- `CanExecute(object?)` — `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked`（第 126 行）。
- `Execute(object?)` — fire-and-forget：`_ = ExecuteAsync(parameter)`（第 128 行）。
- `ExecuteAsync(object?)` — 创建 `CommandEventArgs(parameter, Created)`（当 `_isCtsNeeded` 时分配一个 `CancellationTokenSource`），触发 `Created`，然后在 `_stateLock` 下：若处于强制锁定则取消该条目（触发 `Canceled`）；若 `_active.Count < _maxConcurrency` 则立即启动；否则入队（触发 `Enqueued`）；最后释放锁并调用 `Notify()`（第 139-174 行）。
- `ExecuteCoreAsync` — 触发 `Started`，用条目的 token（或 `_defct`）调用命令，然后触发 `Completed` / `Canceled`（捕获 `OperationCanceledException`）/ `Failed`（捕获其它 `Exception`，带 `CommandEventArgs.Exception`）；最后 `OnExecutionCompletedAsync` 移除条目、触发 `Exited`、触发 `CanExecuteChanged` 并排空队列（第 176-222 行）。
- `LockAsync` / `UnLockAsync` — 切换 `_isForceLocked`、通知，并且（`UnLock` 时）排空队列（第 224-253 行）。
- `InterruptAsync` — 强制锁定、快照并清空活动列表、逐个取消条目的 CTS 并触发 `Canceled`、然后解锁（第 255-279 行）。
- `ClearAsync` — 强制锁定、快照活动列表并把所有待处理条目出队（每个触发 `Dequeued`）、取消所有条目并触发 `Canceled`、然后解锁（第 281-313 行）。
- `ContinueAsync` — 若未强制锁定则排空队列（第 315-329 行）。
- `ChangeSemaphoreAsync` — `< 1` 时忽略，更新 `_maxConcurrency`，排空队列（第 331-347 行）。
- `TryStartPendingAsync` — 在 `_stateLock` 下，当未强制锁定时把最多 `_maxConcurrency` 个排队条目移入 `_active`；每个触发 `Dequeued` 并启动（第 349-377 行）。
- `Notify()` — 触发 `CanExecuteChanged`（第 130 行）。事件触发是异常安全的：`RaiseCommandEvent` 吞掉订阅者异常（第 114-123 行）。

**测试证据：** `VeloxCommandTests` — `Execute_SyncAction_Completes`、`Execute_ActionWithParameter_ReceivesParameter`、`Execute_AsyncFunc_Completes`、`CanExecute_NoPredicate_ReturnsTrue`、`CanExecute_WithPredicate_RespectsIt`、`CreateTaskOnlyWithParameter_Works`（`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`，第 8-82 行）。

**生成的命令属性模板**（`CommandWriter.cs`，第 154-186 行；`canValidate: true` 分支，重新缩进）：

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

`canValidate: false` 分支使用 `canExecute: _ => true`（第 172-186 行）。
