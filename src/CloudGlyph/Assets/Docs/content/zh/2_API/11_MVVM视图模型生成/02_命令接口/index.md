# 命令接口

接口拆分让命令保持可绑定，同时让可选能力保持增量。每条生成命令都以上述某个接口的形式返回。

## VeloxDev.MVVM

### 接口：IVeloxCommand

可绑定的基础接口，扩展 `System.Windows.Input.ICommand`。

**签名：** `public interface IVeloxCommand : ICommand`

**事件**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Created` | `event CommandEventHandler?` | 调用被接受。 |
| `Enqueued` | `event CommandEventHandler?` | 调用在等待空位。 |
| `Dequeued` | `event CommandEventHandler?` | 排队调用离开队列并开始。 |
| `Started` | `event CommandEventHandler?` | 主体开始运行。 |
| `Completed` | `event CommandEventHandler?` | 主体无异常完成。 |
| `Failed` | `event CommandEventHandler?` | 主体抛出异常。 |
| `Canceled` | `event CommandEventHandler?` | 执行被取消。 |
| `Exited` | `event CommandEventHandler?` | 执行离开管线，无论结局。 |

**方法**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Lock` | `void Lock()` | 拒绝新执行并停住队列。 |
| `Unlock` | `void Unlock()` | 恢复命令并启动排队工作。 |
| `Notify` | `void Notify()` | 触发 `CanExecuteChanged`。 |
| `Clear` | `void Clear()` | 取消运行中执行并丢弃排队执行。 |
| `Interrupt` | `void Interrupt()` | 取消运行中执行，保留队列。 |
| `Continue` | `void Continue()` | 未锁定时启动排队工作。 |
| `ChangeSemaphore` | `void ChangeSemaphore(int semaphore)` | 改变并发上限。 |
| `ExecuteAsync` | `Task ExecuteAsync(object? parameter)` | 启动执行；被接受后返回。 |
| `LockAsync` | `Task LockAsync()` | 可等待的 `Lock`。 |
| `UnlockAsync` | `Task UnlockAsync()` | 可等待的 `Unlock`。 |
| `ClearAsync` | `Task ClearAsync()` | 可等待的 `Clear`。 |
| `InterruptAsync` | `Task InterruptAsync()` | 可等待的 `Interrupt`。 |
| `ContinueAsync` | `Task ContinueAsync()` | 可等待的 `Continue`。 |
| `ChangeSemaphoreAsync` | `Task ChangeSemaphoreAsync(int semaphore)` | 可等待的 `ChangeSemaphore`。 |

### 接口：IVeloxCommand<TParam, TResult>

在 `IVeloxCommand` 之上的强类型重载。派生自它可保持命令可绑定。

**签名：** `public interface IVeloxCommand<TParam, TResult> : IVeloxCommand`

| 成员 | 签名 | 说明 |
|---|---|---|
| `CanExecute` | `bool CanExecute(TParam parameter)` | 只反映谓词与锁，绝不反映队列。 |
| `Execute` | `void Execute(TParam parameter)` | 启动执行。 |
| `ExecuteAsync` | `Task ExecuteAsync(TParam parameter)` | 启动执行。 |
| `ExecuteAsync` | `Task<TResult> ExecuteAsync(TParam parameter, CancellationToken cancellationToken)` | 等待本次执行并返回其值。 |
| `Execute` | `void Execute(TParam parameter, out TResult result)` | 阻塞形式；在同一命令主体内调用会死锁。 |

元数族为 2–15 个参数增加 `IVeloxCommand<TParam1, …, TParamN, TResult>`，每个都有同样的五个成员。

### 接口：IVeloxCommandStatus

只读队列状态，`CanExecute` 无法表达。

**签名：** `public interface IVeloxCommandStatus`

| 成员 | 类型 | 说明 |
|---|---|---|
| `IsBusy` | `bool` | 有执行正在运行或排队。 |
| `ActiveCount` | `int` | 当前运行数。 |
| `PendingCount` | `int` | 等待空位的调用数。 |

### 接口：IVeloxCommandResult

返回主体产出的值。

**签名：** `public interface IVeloxCommandResult`

| 成员 | 签名 | 说明 |
|---|---|---|
| `ExecuteAsync` | `Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)` | 等待本次执行；返回装箱的主体值。 |
| `Execute` | `void Execute(object? parameter, out object? result)` | 阻塞形式。 |

`CancellationToken` 参数刻意没有默认值，因此单参数 `IVeloxCommand.ExecuteAsync` 永不歧义。

### 接口：IVeloxCommandCompletion

报告某一次具体执行如何结束，包括被拒绝与被丢弃的调用。

**签名：** `public interface IVeloxCommandCompletion`

| 成员 | 签名 | 说明 |
|---|---|---|
| `ExecuteAndWaitAsync` | `Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)` | 在本次执行结束或调用方令牌触发时完成。 |

### 接口：IVeloxCommandEvents<TParam, TResult>

强类型生命周期事件。以显式实现方式存在，使 `object?` 形状的事件保留类级名称。通过此接口类型的引用订阅可收到未装箱载荷。

**签名：** `public interface IVeloxCommandEvents<TParam, TResult>`

成员：`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`，均为 `event CommandEventHandler<TParam, TResult>?`。

### 类：VeloxCommandExtensions

从生成的命令属性所声明的接口类型访问可选能力。

**签名：** `public static class VeloxCommandExtensions`

| 成员 | 签名 | 说明 |
|---|---|---|
| `ExecuteAndWaitAsync` | `static Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default)` | 实例未实现 `IVeloxCommandCompletion` 时抛 `NotSupportedException`。 |
| `IsBusy` | `static bool IsBusy(this IVeloxCommand command)` | 缺少 `IVeloxCommandStatus` 时抛 `NotSupportedException`。 |
| `ActiveCount` | `static int ActiveCount(this IVeloxCommand command)` | 同上。 |
| `PendingCount` | `static int PendingCount(this IVeloxCommand command)` | 同上。 |

四者遇到 `null` 命令都抛 `ArgumentNullException`。

## 示例

```csharp
using System;
using VeloxDev.MVVM;

IVeloxCommand command = note.PromoteCommand;

Console.WriteLine(command.IsBusy());                 // 经 IVeloxCommandStatus 的扩展
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.Outcome);               // Completed / Canceled / Refused
```

## 说明

- 可选接口独立存在，使增加能力永不破坏手写的 `IVeloxCommand` 实现；`net461` 与 `netstandard2.0` 没有默认接口成员来缓冲新增。
- 强类型命令仍可通过继承来的 `object?` 重载到达，因此传错类型会编译通过，并以携带 `InvalidCastException` 的 `CommandOutcome.Failed` 执行结束。
