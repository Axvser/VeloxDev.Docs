# MVVM — 等待命令与读取状态

`ExecuteAsync` 在调用被**受理**（入队或开始）时就返回。这是即发即忘型 `ICommand` 的正确契约，但它留下两个问题没答：“**这一次**调用是怎么结束的？”以及“这条命令现在忙不忙？”。前者由返回 `CommandCompletion` 的 `ExecuteAndWaitAsync` 回答，后者由 `IsBusy`、`ActiveCount`、`PendingCount` 回答。

## 1. 等待一次执行

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.MVVM;

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

`ExecuteAndWaitAsync` 定义在 `IVeloxCommandCompletion` 上；`VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, ...)` 是把这一能力从“生成属性所声明的接口类型”上取到的桥接扩展。`VeloxCommand` 同时实现这三个接口，因此对生成命令而言扩展总能找到该能力。

**预期结果：** 被 await 的值描述的是**这一次**执行。方法体正常返回时 `Outcome` 为 `CommandOutcome.Completed`、`Succeeded` 为 `true`（实测输出：`Increment -> Completed (Succeeded=True)`）。

## 2. 一次执行的所有结束方式

| `CommandOutcome` | 含义 |
|---|---|
| `Completed` | 方法体跑完且未抛异常 |
| `Failed` | 方法体抛异常 —— `Exception` 携带它 |
| `Canceled` | 运行被取消（中断、清空，或方法体遵守 token），**或**调用在排队期间被清空队列丢弃 |
| `Refused` | 因命令被锁定而从未运行 |

最值得单独说明的是 `Refused`：它**没有**对应的 `CommandEventType`。被拒绝的执行通过事件流上报的是 `Canceled`，且永远不到达 `Exited`，因此单看事件流无法把“被拒绝”与“被取消”区分开。`ExecuteAndWaitAsync` 是观察它的唯一途径。

正因为被拒绝或被清空的调用从不触发 `Exited`，用 `Exited` + `Failed` 手搓的等待恰好会在这两种情况下永久挂起 —— 这也正是该 API 存在的原因。

**预期结果：** 在命令被锁定期间，被 await 的调用会立即返回 `Refused`（实测输出：`while locked -> Refused`），而不是永远不完成。

## 3. 等待自身的取消令牌

`CancellationToken` 重载**只放弃等待** —— 不取消执行：

```csharp
using var cts = new CancellationTokenSource();
var running = command.ExecuteAndWaitAsync(null, cts.Token);
cts.Cancel();                 // await 抛 OperationCanceledException
await command.InterruptAsync(); // 真正停止工作的是这个
```

要停止已在途的工作，请使用 `Interrupt` 或 `Clear`（见上一页）。只有调用方自己的 token 会让 await 抛异常；被取消的**执行**是正常返回，携带 `CommandOutcome.Canceled`。

**预期结果：** 取消等待会抛 `OperationCanceledException`，而 `ActiveCount` 保持原值 —— 执行未受任何影响。

## 4. 读取状态

`ICommand.CanExecute` 反映的是谓词与锁，从不反映队列，因此唯一槽位被占用的命令依然报告自己可执行 —— 只绑定 `CanExecute` 的按钮看起来可用，按下去却什么都不发生。以下成员回应这个问题：

| 成员 | 含义 |
|---|---|
| `IsBusy` | 有执行正在运行**或**正在等待空闲槽位 |
| `ActiveCount` | 此刻正在运行的执行数 |
| `PendingCount` | 正在等待空闲槽位的调用数 |

它们定义在 `IVeloxCommandStatus` 上，同样通过扩展类从 `IVeloxCommand` 取到：

```csharp
Console.WriteLine(command.IsBusy());       // bool
Console.WriteLine(command.ActiveCount());  // int
Console.WriteLine(command.PendingCount()); // int
```

读取时不获取命令内部的锁，因此并发更新可能让它们滞后一步 —— 这是刻意的，因为属性 getter 不应阻塞。当目的是“阻止用户按下已经排队的按钮”时，绑定 `IsBusy` 而不是 `CanExecute`。

**预期结果：** 空闲命令报告 `IsBusy=false, ActiveCount=0, PendingCount=0`（实测输出）；槽位被占用的命令报告 `IsBusy=true`，而 `CanExecute(null)` 仍为 `true`。

## 5. 手写实现必须显式选择加入

`IVeloxCommandCompletion` 与 `IVeloxCommandStatus` 之所以是独立接口，正是为了让“新增它们”不破坏任何既有实现者。因此，只实现 `IVeloxCommand` 的手写实现必须明确表态：扩展方法会抛 `NotSupportedException`，消息中指明缺失的接口；对 `null` 命令则抛 `ArgumentNullException`。由 `VeloxCommand` 构建的所有命令都完整支持这些能力。

**预期结果：** 对仅实现 `IVeloxCommand` 的实现，`somePlainCommand.IsBusy()`、`.ActiveCount()`、`.PendingCount()` 与 `.ExecuteAndWaitAsync(null)` 全部抛 `NotSupportedException`。

## 运行声明

- ✅ 2026-10-01 实际构建并运行过。一个引用 `VeloxDev.Core`（Debug 项目引用）与生成器的临时控制台项目用 `dotnet run -c Debug` 执行。录制输出 —— 下面三行正是本页的验证：

  ```text
  Increment -> Completed (Succeeded=True)
  status: IsBusy=False, Active=0, Pending=0
  while locked -> Refused
  ```

  程序先 await 了两条命令，打印状态三元组，然后用 `await vm.IncrementCommand.LockAsync()` 锁定命令并 await 第三次调用，结果为 `Refused`。

- 第 3 节的 token 语义与第 5 节的 `NotSupportedException` 行为本次**未**执行；它们转录自 `VeloxCommand.cs`、`VeloxCommandExtensions.cs`，并由 `Src/Core/VeloxDev.Core.Test/MVVM/` 下的 `VeloxCommandCompletionTests` / `VeloxCommandStatusTests` 钉住。
