# MVVM — 等待命令与读取状态

`ExecuteAsync` 在调用被**受理**（入队或启动）后立即返回。另外两个问题各有自己的 API："**这一次**调用是怎么结束的？"（`ExecuteAndWaitAsync` → `CommandCompletion`）与"命令现在忙吗？"（`IsBusy` / `ActiveCount` / `PendingCount`）。第三个问题只对强类型命令成立："方法体返回了什么？"（`IVeloxCommandResult` 与 `IVeloxCommand<TParam, TResult>`）。

## 1. 等待一次执行

```csharp
static async Task RunAsync(IVeloxCommand command)
{
    CommandCompletion completion = await command.ExecuteAndWaitAsync(null);

    Console.WriteLine(completion.Outcome);   // Completed / Failed / Canceled / Refused
    Console.WriteLine(completion.Succeeded); // 仅 Completed 为 true
    if (completion.Exception is not null)
    {
        Console.WriteLine(completion.Exception.Message);
    }
}
```

`ExecuteAndWaitAsync` 声明在 `IVeloxCommandCompletion` 上；扩展方法 `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, ...)` 从生成属性所声明的接口类型到达它。`VeloxCommand` 构造的每条命令都实现该接口。

**预期结果：** 等待值描述这一次执行。正常返回的方法体给出 `Outcome == Completed`、`Succeeded == true`。

## 2. 一次执行的所有结局

| `CommandOutcome` | 含义 |
| --- | --- |
| `Completed` | 方法体正常跑完 |
| `Failed` | 方法体抛出异常；`Exception` 携带它 |
| `Canceled` | 运行被取消，或在 `Clear` 清空队列时仍在排队 |
| `Refused` | 命令被锁定，调用从未运行 |

`Refused` 没有对应的 `CommandEventType`：被拒绝的执行通过事件上报 `Canceled`，且永不到达 `Exited`，所以仅凭事件流无法把它与取消区分开。

正因如此，用 `Exited` + `Failed` 手写的等待会在这两种情况下永久挂起。

**预期结果：** 命令锁定时，等待的调用立即返回 `Refused`，而不是永远不完成。

## 3. 取得方法体的返回值

返回 `Task<T>` 或 `ValueTask<T>` 的方法体会填充结果通道：

```csharp
CommandCompletion completion = await command.ExecuteAndWaitAsync(10);
int value = completion.GetResultOrThrow<int>();   // 结局不是 Completed 时抛异常
```

`CommandCompletion.Result` 是装箱后的值（方法体没有返回值时为 `null`）。`GetResultOrThrow()` 重新抛出原始异常；`GetResultOrThrow<TR>()` 在值不是 `TR` 时还会抛 `InvalidCastException`。

强类型命令无需装箱地暴露返回值：

```csharp
IVeloxCommand<NotePayload, int> measure = vm.MeasureNoteCommand;
int weight = await measure.ExecuteAsync(note, CancellationToken.None);
measure.Execute(note, out int alsoWeight);        // 同步版本
```

`IVeloxCommandResult.ExecuteAsync(object? parameter, CancellationToken cancellationToken)` 是同一操作的未强类型形态。

**预期结果：** 成功的 `Task<int>` 方法体返回其值；失败时以原始异常实例与堆栈重新抛出；错误的 `TR` 抛 `InvalidCastException`。

## 4. 等待自身的取消令牌

`CancellationToken` 重载只放弃**等待**，不取消执行：

```csharp
using var cts = new CancellationTokenSource();
var running = command.ExecuteAndWaitAsync(null, cts.Token);
cts.Cancel();                    // await 抛 OperationCanceledException
await command.InterruptAsync();  // 真正停止工作的是这里
```

**预期结果：** 取消等待会抛 `OperationCanceledException`，而 `ActiveCount` 保持不变。

## 5. 读取状态

`ICommand.CanExecute` 只反映谓词与锁，从不反映队列。以下成员回答队列问题：

| 成员 | 含义 |
| --- | --- |
| `IsBusy` | 有执行正在运行**或**在等待空闲槽位 |
| `ActiveCount` | 当前正在运行的执行数 |
| `PendingCount` | 正在等待空闲槽位的调用数 |

它们位于 `IVeloxCommandStatus`，通过 `VeloxCommandExtensions` 从 `IVeloxCommand` 到达：

```csharp
Console.WriteLine(command.IsBusy());       // bool
Console.WriteLine(command.ActiveCount());  // int
Console.WriteLine(command.PendingCount()); // int
```

读取时不取内部锁，因此并发更新可能让值落后一步 —— 这是刻意的，因为属性 getter 不应阻塞。当目的是阻止用户按下工作已排队的按钮时，绑定 `IsBusy` 而不是 `CanExecute`。

**预期结果：** 空闲命令报告 `IsBusy=false, ActiveCount=0, PendingCount=0`；槽位被占用的命令报告 `IsBusy=true`，而 `CanExecute(null)` 仍为 `true`。

## 6. 手写实现必须显式选择

`IVeloxCommandCompletion`、`IVeloxCommandResult`、`IVeloxCommandStatus` 与 `IVeloxCommandEvents<TParam, TResult>` 都是独立接口，这样新增能力不会破坏已有实现者。只实现 `IVeloxCommand` 的手写类会让扩展方法抛出 `NotSupportedException` 并指出缺失的接口；`null` 命令抛 `ArgumentNullException`。

**预期结果：** 对只实现 `IVeloxCommand` 的类，`plainCommand.IsBusy()`、`.ActiveCount()`、`.PendingCount()` 与 `.ExecuteAndWaitAsync(null)` 都抛 `NotSupportedException`。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `Interfaces/MVVM/{IVeloxCommandCompletion,IVeloxCommandResult,IVeloxCommandStatus}.cs`、`MVVM/{CommandCompletion,VeloxCommandExtensions}.cs` 以及 `Src/Core/VeloxDev.Core.Test/MVVM/` 下的测试做了静态核对。
