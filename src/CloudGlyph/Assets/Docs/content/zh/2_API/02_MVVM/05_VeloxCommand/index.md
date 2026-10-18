# MVVM — `VeloxCommand`

`VeloxDev.MVVM.VeloxCommand`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是 `object?` 形态的命令。它派生自 `CommandPipeline<object?, object?>`，后者提供所有接口与成员；`VeloxCommand` 自身只增加决定"方法体是否接收 token"与"是否捕获返回值"的构造函数与工厂。

## Class: `VeloxCommand`

**Signature**

```csharp
public class VeloxCommand : CommandPipeline<object?, object?>
{
    public VeloxCommand(
        Func<object?, CancellationToken, Task> command,
        Predicate<object?>? canExecute = null,
        int semaphore = 1);

    public VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1);
    public VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1);
    public VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1);
}
```

**基类型：** `CommandPipeline<object?, object?>`，从中继承 `IVeloxCommand`（因而继承 `ICommand`）、`IVeloxCommandCompletion`、`IVeloxCommandResult`、`IVeloxCommandStatus`、`IVeloxCommandEvents<object?, object?>` 与 `IDisposable`。

**密封：** 否。强类型族（`VeloxCommand<TParam, TResult>` 及 arity 变体）是独立的类。

## 成员索引

| 种类 | 成员 | 页面 |
| --- | --- | --- |
| 构造函数 | `(Func<object?, CancellationToken, Task>, …)`、`(Func<Task>, …)`、`(Action<object?>, …)`、`(Action, …)` | [构造](00_构造/index.md) |
| 静态工厂 | `CreateTaskOnlyWithResult`、`CreateTaskWithResult`、`CreateTaskOnlyWithParameter`、`CreateTaskOnlyWithCancellationToken`、`CreateTypedTaskOnlyWithParameter<T>`、`CreateTypedWithParameter<T>`、两个 `ValueTask` 工厂（条件编译） | [构造](00_构造/index.md) |
| 执行 | `CanExecute`、`Execute`、`ExecuteAsync(object?)`、`ExecuteAsync(object?, CancellationToken)`、`Execute(object?, out object?)`、`ExecuteAndWaitAsync`、`Notify` | [执行](01_执行/index.md) |
| 生命周期控制 | `Lock` / `LockAsync`、`Unlock` / `UnlockAsync`、`Interrupt` / `InterruptAsync`、`Clear` / `ClearAsync`、`Continue` / `ContinueAsync`、`ChangeSemaphore` / `ChangeSemaphoreAsync` | [控制](02_控制/index.md) |
| 属性 | `EventContext`、`IsBusy`、`ActiveCount`、`PendingCount` | [状态、事件与释放](03_状态事件与释放/index.md) |
| 事件 | 8 个生命周期事件、`CanExecuteChanged`、静态 `HandlerException`、显式实现的强类型事件 | [状态、事件与释放](03_状态事件与释放/index.md) |
| 拆除 | `Dispose` | [状态、事件与释放](03_状态事件与释放/index.md) |

## 行为

- **线程安全。** 内部状态由私有 `SemaphoreSlim(1,1)` 保护，每次内部 await 使用 `ConfigureAwait(false)`。持锁期间不运行用户代码。
- **有界且排队。** `semaphore` 是并发容量。无法立即开始的调用会入队而非被丢弃。
- **可观察。** 每次执行上报八个 `CommandEventType` 阶段；`Execute` / `ExecuteAsync` 在受理后返回。
- **无人观察时零成本。** 没有订阅者的阶段不构造 `CommandEventArgs`（`CommandAllocationTests`）。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var called = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
var command = new VeloxCommand(() => called.TrySetResult(true));
var recorder = new CommandEventRecorder(command);

command.Execute(null);
await recorder.FirstExit;

Assert.IsTrue(called.Task.IsCompleted, "the body ran to completion");
```

## 它从哪里来

你很少手工构造它：`[VeloxCommand]` 会让 Command 生成器产出一个懒加载属性，其 getter 调用上述某个构造函数或工厂（见 `14_Command` 页）。直接构造是测试验证运行时的方式，也是视图模型为不想另加标注的方法构建命令的方式。
