# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是 `IVeloxCommand`、`IVeloxCommandCompletion` 与 `IVeloxCommandStatus` 的密封实现，并额外实现 `IDisposable`。它是 Command 生成器唯一会构造的类型。

## Class: `VeloxCommand`

**Signature**

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand, IVeloxCommandCompletion, IVeloxCommandStatus, IDisposable
```

**实现：** `IVeloxCommand`（其继承 `System.Windows.Input.ICommand`）、`IVeloxCommandCompletion`、`IVeloxCommandStatus`、`IDisposable`。

**密封：** 是。

## 成员索引

| 种类 | 成员 | 页面 |
|---|---|---|
| 构造函数 | 主构造函数 `(Func<object?, CancellationToken, Task>, …)`、`(Func<Task>, …)`、`(Action<object?>, …)`、`(Action, …)` | [构造](00_构造/index.md) |
| 静态工厂 | `CreateTaskOnlyWithParameter`、`CreateTaskOnlyWithCancellationToken`、`CreateTaskOnlyWithValueTaskParameter`、`CreateTaskOnlyWithValueTaskCancellationToken` | [构造](00_构造/index.md) |
| 执行 | `CanExecute`、`Execute`、`ExecuteAsync`、`ExecuteAndWaitAsync`、`Notify` | [执行](01_执行/index.md) |
| 生命周期控制 | `Lock` / `LockAsync`、`Unlock` / `UnlockAsync`、`Interrupt` / `InterruptAsync`、`Clear` / `ClearAsync`、`Continue` / `ContinueAsync`、`ChangeSemaphore` / `ChangeSemaphoreAsync` | [控制](02_控制/index.md) |
| 属性 | `EventContext`、`IsBusy`、`ActiveCount`、`PendingCount` | [状态、事件与释放](03_状态事件与释放/index.md) |
| 事件 | 8 个生命周期事件（`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`）、`CanExecuteChanged`、静态 `HandlerException` | [状态、事件与释放](03_状态事件与释放/index.md) |
| 拆除 | `Dispose` | [状态、事件与释放](03_状态事件与释放/index.md) |

## 行为

- **线程安全。** 所有内部状态（`_pendingQueue`、`_active`、`_isForceLocked`、`_maxConcurrency`）由私有 `SemaphoreSlim(1,1)` 保护，且每次内部 await 都使用 `ConfigureAwait(false)`。持锁期间不运行任何用户代码，因此阻塞在命令上的处理器不会把命令锁死。
- **有界且会排队。** `semaphore` 是并发容量。无法立即开始的调用会入队而非被丢弃，并在槽位释放后开始。
- **可观察。** 每次执行通过对应事件上报八个 `CommandEventType` 阶段；`Execute` / `ExecuteAsync` 在执行被受理后返回，而非结束时。
- **无人观察时零成本。** 没有订阅者的阶段不会构造它的 `CommandEventArgs`，因此无订阅者的命令每次执行分配的内存少于订阅了全部事件的命令（`CommandAllocationTests`）。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 19-29
var called = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
var command = new VeloxCommand(() => called.TrySetResult(true));
var recorder = new CommandEventRecorder(command);

command.Execute(null);
await recorder.FirstExit;

Assert.IsTrue(called.Task.IsCompleted, "the body ran to completion");
```

## 它从哪里来

你很少手工构造它：`[VeloxCommand]` 会让 Command 生成器产出一个懒加载属性，其 getter 调用上述某个构造函数或工厂（见 `14_Command` 页）。直接构造是测试用来验证运行时的方式，也是视图模型为“不想另加标注的方法”构建命令的方式。
