# 运行时引擎

引擎逐项遍历编译图。`ChainSegment` 按序驱动节点；`BranchSegment` 先驱动路由器再走选中选项；`ParallelSegment` 让每个分支从同一载荷开始。节点返回值成为下一节点的载荷。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`（引擎与运行结局）与 `VeloxDev.WorkflowSystem`（数据流契约）。

## RuntimeEngine

**签名：** `sealed class RuntimeEngine`

### RunAsync

**签名：** `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct, ExecutionCheckpoint? resumeFrom = null)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `graph` | `CompiledGraph` | 要驱动的图；null 立即返回。 |
| `context` | `IRuntimeContext` | 会话；null 立即返回。 |
| `ct` | `CancellationToken` | 取消会在下一个节点边界停止运行。 |
| `resumeFrom` | `ExecutionCheckpoint?` | 要接续的检查点；其形状必须与 `graph` 一致。 |

**返回：** `Task` —— 运行结束时完成。结果写入会话：`Status`、`EndedWithError`、`Outcome`、`Data`、`Attempt`、`Logs`。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `InvalidOperationException` | `resumeFrom` 来自另一张图，或超过重定向上限（50）。 |

检查点形状在触碰会话**之前**校验，因此被拒绝的恢复会让 `Status` 停在 `Idle`。

## 执行语义

- **链**按段序运行。后续趟次会跳过 `Order` 低于重定向目标的节点；被跳过节点的已登记产物会重新写回 `Data`，使目标拿到与上一趟相同的载荷。
- **分支**先驱动路由器，再用 `Equals(option.Key, key)` 选选项。缺失或终止选项以 `Completed` 结束运行。
- **扇出**分支以交错异步操作并发运行，各自拥有 `BranchRuntimeContext`（载荷与重定向请求分支私有；日志、身份与产物表共享）。按分支顺序第一个重定向请求胜出；任一分支命中终止分支会结束整轮运行。
- **汇合**由编译器识别：节点 `InputNodes` 多于一项时，`Data` 被替换为上游产物上的 `GroupData`。
- **失败**：`Warn` 是提醒，值继续流动；`Error` 或未捕获异常算作 `null` 结果，并经 `IRedirectable`/`HostRedirect` 重定向，或以上 `EndedWithError` 与 `Status = "Stopped"` 结束流程。
- **取消**设 `Status = "Stopped"`、`EndedWithError = false`，因此 `Outcome` 为 `Cancelled`。
- **Attempt** 计过图趟数；重定向加一，重试不加。

## RunOutcome

**签名：** `enum RunOutcome`

| 值 | 条件 |
| --- | --- |
| `Unknown = 0` | 未开始或仍在运行。 |
| `Completed` | `Status == "Completed"`；每个项都走完。 |
| `Cancelled` | `Status == "Stopped"` 且 `EndedWithError == false`。 |
| `Failed` | `Status == "Stopped"` 且 `EndedWithError == true`。 |

刻意没有 `Stopped` 成员：产生该字符串的两条路径已分别由 `Cancelled` 与 `Failed` 覆盖。

## 数据流契约

### IContext

**签名：** `interface IContext` —— `object? Data { get; }`。

### IAccessContext

**签名：** `interface IAccessContext : IContext`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `IsCompilePhase` | `bool` | 编译期静态检查为 `true`，运行期为 `false`。 |
| `Sender` | `ISlotComponent?` | 上游输出插槽。 |
| `Receiver` | `ISlotComponent?` | 下游输入插槽。 |

### ITaskContext

**签名：** `interface ITaskContext : IAccessContext` —— 不增加成员；它是 `ReceiveAsync` 收到的载荷形状。

### TaskContext

**签名：** `readonly struct TaskContext : ITaskContext`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `TaskContext(object? data = null, ISlotComponent? sender = null, ISlotComponent? receiver = null)` | 构造函数 | 携带载荷与边两端。 |
| `IsCompilePhase` | `bool` | 恒为 `false`。 |
| `Data` / `Sender` / `Receiver` | | 存储值；均可为空。 |
| `Deconstruct(out object?, out ISlotComponent?, out ISlotComponent?)` | `void` | 类元组解包。 |

## IGroupData 与 GroupData

**签名：** `interface IGroupData : IReadOnlyDictionary<INodeComponent, object?>`

`GroupData`（`readonly struct`，实现 `IGroupData`）包装一个只读字典。键是**源节点引用**，值是该节点本轮产物。本趟未被驱动的上游不在字典里，因此 `TryGetValue` 返回 `false` 而非陈旧值；索引器对缺失键抛 `KeyNotFoundException`。

```csharp
var group = (IGroupData)ctx.Data!;
foreach (var pair in group)
    Console.WriteLine($"{pair.Key.GetType().Name}={pair.Value}");
```

## 示例

```csharp
var graph = (await new CompilerViewModel().CompileAsync(start, CompileRole.Root))[0];
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);

Console.WriteLine($"{session.Status} / {session.Outcome} / attempt {session.Attempt}");
Console.WriteLine(session.Data);
```
