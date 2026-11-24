# 命令运行时

每条生成命令背后的有界、排队、可取消命令管线。在代码中直接构造命令而非生成时，完全可以单独使用。

## VeloxDev.MVVM

### 枚举：CommandOutcome

| 成员 | 值 | 含义 |
|---|---|---|
| `Completed` | 0 | 主体无异常地运行完毕。 |
| `Failed` | 1 | 主体抛出异常。 |
| `Canceled` | 2 | 被 `Interrupt` / `Clear` 取消、主体响应了令牌，或从队列中被丢弃。 |
| `Refused` | 3 | 命令已锁定，调用从未运行。 |

### 结构：CommandCompletion

`ExecuteAndWaitAsync` 返回的单次执行结果。

**签名：** `public readonly struct CommandCompletion`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Outcome` | `CommandOutcome` | 执行如何结束。 |
| `Exception` | `Exception?` | 失败异常，仅 `Failed` 时非空。 |
| `Result` | `object?` | 主体返回值，装箱；无返回值时为 `null`。 |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`。 |

| 方法 | 签名 | 说明 |
|---|---|---|
| `GetResultOrThrow` | `object? GetResultOrThrow()` | 返回 `Result`；否则抛出失败、`Canceled` 的 `OperationCanceledException`，或 `Refused` 的 `InvalidOperationException`。 |
| `GetResultOrThrow<TR>` | `TR GetResultOrThrow<TR>()` | 强类型形式；可能抛 `InvalidCastException`。 |
| `ToString` | `string ToString()` | 结果，带异常消息（若有）。 |

### 枚举：CommandEventType

`None`、`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`。

`Exited` 只表示执行离开了管线，不是成功信号。`Failed` 是唯一携带异常的阶段。

### 委托：CommandEventHandler

`public delegate void CommandEventHandler(CommandEventArgs e)`

### 类：CommandEventArgs

**签名：** `public class CommandEventArgs(object? parameter, CommandEventType type, Exception? ex = null, CancellationTokenSource? cts = null)`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Parameter` | `virtual object?` | 传给 `ICommand.Execute` 的参数；读取值类型会装箱。 |
| `Exception` | `Exception?` | 仅 `Failed` 时填充。 |
| `EventType` | `CommandEventType` | 本实例报告阶段。 |

`With(CommandEventType newType, Exception? ex = null)` 把同一次执行投影到另一阶段，保留参数与取消源。

### 类：CommandEventArgs<TParam, TResult>

强类型载荷，派生自 `CommandEventArgs`。

**签名：** `public sealed class CommandEventArgs<TParam, TResult> : CommandEventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `TypedParameter` | `TParam` | 自身类型的参数；若以其他类型装箱到达则抛 `InvalidCastException`。 |
| `TypedResult` | `TResult` | 执行结束后的主体返回值。 |
| `Parameter` | `override object?` | 强类型参数，仅在读取时装箱。 |
| `With` | `new CommandEventArgs<TParam, TResult> With(CommandEventType newType, Exception? ex = null)` | 把强类型载荷投影到另一阶段。 |

### 委托：CommandEventHandler<TParam, TResult>

`public delegate void CommandEventHandler<TParam, TResult>(CommandEventArgs<TParam, TResult> e)`

### 类：CommandPipeline<TParam, TResult>

共享实现。抽象类；可派生，或直接使用 `VeloxCommand` / `VeloxCommand<TParam, TResult>`。

**签名：**
`public abstract class CommandPipeline<TParam, TResult> : IVeloxCommand, IVeloxCommandCompletion, IVeloxCommandStatus, IVeloxCommandResult, IVeloxCommandEvents<TParam, TResult>, IDisposable`

**构造函数（protected）**
`CommandPipeline(Func<TParam, CancellationToken, Task> command, Func<TParam, CancellationToken, Task<TResult>>? resultCommand, Predicate<TParam>? canExecute, int semaphore, bool isCtsNeeded)`

**事件**

| 成员 | 签名 | 说明 |
|---|---|---|
| `HandlerException` | `static event Action<Exception>?` | 报告抛异常的订阅者。进程级，不按泛型闭合各持一份。 |
| `CanExecuteChanged` | `event EventHandler?` | 标准 `ICommand` 通知。 |
| `Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited` | `event CommandEventHandler?` | 八个生命周期阶段。 |

**属性**

| 成员 | 类型 | 说明 |
|---|---|---|
| `EventContext` | `SynchronizationContext?` | 设置后生命周期事件投递到该上下文；`null` 表示在管线线程上直接触发。 |
| `IsBusy` | `bool` | 有执行正在运行或排队。 |
| `ActiveCount` | `int` | 当前运行数。 |
| `PendingCount` | `int` | 等待空位的调用数。 |

**方法**

| 成员 | 签名 | 说明 |
|---|---|---|
| `CanExecute` | `bool CanExecute(object? parameter)` | `ICommand` 面；参数类型不符也不抛异常。 |
| `Execute` | `void Execute(object? parameter)` | 启动执行；被接受后立即返回。 |
| `Notify` | `void Notify()` | 触发 `CanExecuteChanged`。 |
| `Lock` / `Unlock` | `void Lock()`、`void Unlock()` | 拒绝 / 恢复执行。 |
| `Interrupt` | `void Interrupt()` | 取消运行中的执行，保留队列。 |
| `Clear` | `void Clear()` | 取消运行中执行并丢弃排队执行。 |
| `Continue` | `void Continue()` | 未锁定时启动排队工作。 |
| `ChangeSemaphore` | `void ChangeSemaphore(int s)` | 改变并发上限；`s < 1` 抛 `ArgumentOutOfRangeException`。 |
| `ExecuteAsync` | `Task ExecuteAsync(object? parameter)` | 启动执行。 |
| `ExecuteAsync` | `Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)` | 等待本次执行并返回装箱值。 |
| `Execute` | `void Execute(object? parameter, out object? result)` | 阻塞式结果形式。 |
| `ExecuteAndWaitAsync` | `Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)` | 报告本次执行如何结束，包括被拒绝与被丢弃的调用。 |
| `LockAsync` / `UnlockAsync` / `InterruptAsync` / `ClearAsync` / `ContinueAsync` / `ChangeSemaphoreAsync` | `Task` | 可等待的对应版本。 |
| `Dispose` | `void Dispose()` | 释放内部锁；终结性。 |

**受保护成员：** `CanExecuteCore(TParam)`、`ExecuteAsyncCore(TParam)`、`ExecuteAndWaitTypedAsync(TParam, CancellationToken)`、`ExecuteAndWaitTyped(TParam)`。

### 类：VeloxCommand

`object?` 形状的命令。

**签名：** `public class VeloxCommand : CommandPipeline<object?, object?>`

**构造函数**

| 签名 |
|---|
| `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)` |

**静态工厂**

| 成员 | 签名 |
|---|---|
| `CreateTaskOnlyWithResult` | `static VeloxCommand CreateTaskOnlyWithResult(Func<object?, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskWithResult` | `static VeloxCommand CreateTaskWithResult(Func<object?, CancellationToken, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithParameter` | `static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTypedTaskOnlyWithParameter<T>` | `static VeloxCommand<T, object?> CreateTypedTaskOnlyWithParameter<T>(Func<T, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)` |
| `CreateTypedWithParameter<T>` | `static VeloxCommand<T, object?> CreateTypedWithParameter<T>(Func<T, CancellationToken, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithValueTaskParameter` | `static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`（不含 `netstandard2.0` / `netframework`） |
| `CreateTaskOnlyWithValueTaskCancellationToken` | `static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`（不含 `netstandard2.0` / `netframework`） |

### 类：VeloxCommand<TParam, TResult>

单参数强类型命令。

**签名：** `public sealed class VeloxCommand<TParam, TResult> : CommandPipeline<TParam, TResult>, IVeloxCommand<TParam, TResult>`

**构造函数**
`public VeloxCommand(Func<TParam, CancellationToken, Task<TResult>> command, Predicate<TParam>? canExecute = null, int semaphore = 1)`

**静态工厂**
`public static VeloxCommand<TParam, TResult> CreateTaskOnlyWithResult(Func<TParam, Task<TResult>> command, Predicate<TParam>? canExecute = null, int semaphore = 1)`

**成员：** `CanExecute(TParam)`、`Execute(TParam)`、`ExecuteAsync(TParam)`、`ExecuteAsync(TParam, CancellationToken)`、`Execute(TParam, out TResult)`。

## 多参数命令族

`CommandArities.cs` 为 2 到 15 的每个参数数量声明一个接口与一个密封类：

- `IVeloxCommand<TParam1, …, TParamN, TResult>`，派生自 `IVeloxCommand`
- `VeloxCommand<TParam1, …, TParamN, TResult>`，派生自 `CommandPipeline<(TParam1, …, TParamN), TResult>`

每个接口声明 `CanExecute(...)`、`Execute(...)`、`ExecuteAsync(...)`、`ExecuteAsync(..., CancellationToken)` 与 `Execute(..., out TResult)`。每个类的构造函数接收 `Func<TParam1, …, TParamN, CancellationToken, Task<TResult>>`、可选 `Func<…, bool>` 校验器与 `int semaphore`，另有 `CreateTaskOnlyWithResult` 工厂及同样的五个成员。参数以 `ValueTuple` 穿过管线，因此强类型路径上不会装箱。无参数命令没有强类型形式；请用 `VeloxCommand`（`object?` 形状）或忽略参数的主体。

## 异常

| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | 命令主体为 `null`。 |
| `ArgumentOutOfRangeException` | 构造或 `ChangeSemaphore` 时 `semaphore < 1`。 |
| `OperationCanceledException` | 调用方的 `CancellationToken` 放弃等待，或被等待的执行被取消。 |
| `InvalidOperationException` | 被等待的执行因命令锁定而被拒绝。 |

## 示例

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.MVVM;

var save = new VeloxCommand(
    async (object? _, CancellationToken ct) => await Task.Delay(50, ct),
    semaphore: 1);

await save.ExecuteAsync(null);
CommandCompletion how = await save.ExecuteAndWaitAsync(null);
Console.WriteLine(how.Outcome);
```

生成的命令属性声明为接口（`IVeloxCommand`），因此此示例显式构造具体类型。特性驱动的路径见 [MVVM 视图模型生成](../../../1_快速开始/11_MVVM视图模型生成/index.md)。
