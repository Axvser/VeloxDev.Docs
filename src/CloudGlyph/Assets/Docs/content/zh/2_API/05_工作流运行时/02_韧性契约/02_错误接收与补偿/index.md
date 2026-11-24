# 错误接收与补偿

引擎已经把每条失败写成日志行。接收器把失败变成记录，补偿器获知一次糟糕运行已经驱动过哪些节点——引擎自己什么都不回滚。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## ExecutionFailurePhase

**签名：** `enum ExecutionFailurePhase`

| 值 | 含义 |
| --- | --- |
| `Node = 0` | 节点抛出或报告错误。 |
| `Router` | 路由器解析键时抛出。 |
| `Redirect` | 节点或宿主策略解析重定向时抛出。 |
| `Run` | 运行本身失败：重定向上限或取消。 |

## ExecutionReportLevel

**签名：** `enum ExecutionReportLevel`

| 值 | 含义 |
| --- | --- |
| `Warning = 0` | 节点调用 `WarnAsync`；没有出错。 |
| `Error` | 节点调用 `ErrorAsync`、抛出，或引擎放弃。 |

引擎自己记录的一切都是错误。

## ExecutionError

**签名：** `readonly record struct ExecutionError(ExecutionFailurePhase Phase, INodeComponent? Node, string Message, Exception? Error, int Attempt, int Order, ExecutionReportLevel Level = ExecutionReportLevel.Error)`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Phase` | `ExecutionFailurePhase` | 失败来源。 |
| `Node` | `INodeComponent?` | 节点；运行级失败为 null。 |
| `Message` | `string` | 引擎记录的消息。 |
| `Error` | `Exception?` | 有异常时的异常。 |
| `Attempt` | `int` | 趟数。 |
| `Order` | `int` | 节点编译顺序，或 `-1`。 |
| `Level` | `ExecutionReportLevel` | 警告或错误。 |

## IExecutionErrorSink

**签名：** `interface IExecutionErrorSink`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `OnErrorAsync(ExecutionError error, CancellationToken cancellationToken)` | `Task` | 每条记录按序调用一次。 |

两条入口：引擎报告自己看到的，节点通过 `ErrorAsync`/`WarnAsync` 报告（会等待接收器）。同步的 `Error`/`Warn` 只写日志，因为它们必须保持不阻塞。接收器抛异常会被吞掉并记录；报告失败不能自己添一条失败。令牌：引擎报告是运行令牌，节点自报是 `CancellationToken.None`。

## DelegateExecutionErrorSink

**签名：** `sealed class DelegateExecutionErrorSink(Action<ExecutionError> observe) : IExecutionErrorSink`

包装同步动作；null 抛 `ArgumentNullException`。

## NodeCompensation

**签名：** `readonly record struct NodeCompensation(INodeComponent Node, object? Output, int Order)`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Node` | `INodeComponent` | 运行驱动过的节点。 |
| `Output` | `object?` | 它产出的值；该次驱动失败时为 null。 |
| `Order` | `int` | 编译顺序，或 `-1`。 |

## IExecutionCompensation

**签名：** `interface IExecutionCompensation`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `CompensateAsync(NodeCompensation compensation, CancellationToken cancellationToken)` | `Task` | 每个驱动节点调用一次，最近优先。 |

- 只在运行以 `Failed` 或 `Cancelled` 收尾时调用；完成的运行不补偿。
- 运行登记过的每个节点都会出现，包括失败的那个（输出为 null）以及重定向前缀保留的节点。
- 按驱动逆序、最近优先；重跑节点只出现一次，位于其最新位置。
- 清理令牌**不是**运行令牌：取消之后那个已取消。
- 补偿抛异常会被记录，其余继续。
- 树的撤销栈不是替代品：它只记录模型结构变更、没有运行边界、也不保证链完整。

## DelegateExecutionCompensation

**签名：** `sealed class DelegateExecutionCompensation(Action<NodeCompensation> compensate) : IExecutionCompensation`

包装同步动作；null 抛 `ArgumentNullException`。

## 示例

```csharp
var compensated = new List<string>();
var session = new RuntimeContext
{
    Data = "seed",
    ErrorSink = new DelegateExecutionErrorSink(e => Console.WriteLine($"{e.Phase}:{e.Level}:{e.Message}")),
    Compensation = new DelegateExecutionCompensation(
        c => compensated.Add($"{c.Node.GetType().Name}:{c.Output ?? "null"}")),
};

await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Outcome} [{string.Join(",", compensated)}]");
```
