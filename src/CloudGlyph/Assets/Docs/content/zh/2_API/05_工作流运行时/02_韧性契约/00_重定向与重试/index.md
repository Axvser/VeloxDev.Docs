# 重定向与重试

抛出的异常是失败驱动；`Error` 调用是刻意的重定向请求。只有抛出会被重试，且仅在配置了重试策略时。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## IRedirectable

**签名：** `interface IRedirectable`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` | `Task<INodeComponent?>` | 返回要回退到的上游节点，或 null 表示拒绝。 |

当驱动报告 `Error` 或抛出时，引擎调用它。返回节点必须是请求节点的**上游**编译节点；引擎把它映射为该节点的编译顺序，在该节点处结束本趟，并从目标起重跑整图，跳过更早节点。位于目标处或其之前的重路由器不再驱动，只重新询问其路由键。

非法目标会被记录并忽略，流程继续。重定向上限为 50 趟。

## NodeFailure

**签名：** `readonly record struct NodeFailure(INodeComponent Node, Exception Error, int RetryNumber, TimeSpan Elapsed)`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Node` | `INodeComponent` | 失败节点。 |
| `Error` | `Exception` | 它抛出的异常。 |
| `RetryNumber` | `int` | 本次决定针对第几次重试；第一次为 `1`。 |
| `Elapsed` | `TimeSpan` | 失败尝试耗时。 |

## INodeRetryPolicy

**签名：** `interface INodeRetryPolicy`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `NextRetryAsync(NodeFailure failure, CancellationToken cancellationToken)` | `Task<TimeSpan?>` | 下一次尝试前的延迟，或 null 把失败交回引擎。 |

- 只有抛出的异常会被重试。调用 `Error`/`Warn` 的节点是在表达控制流，不是待重试的失败。
- `RetryNumber` 从 `1` 起；总是返回延迟的策略会永远重试，因为运行没有其他上限。
- 重试**不是**新一趟：`IRuntimeContext.Attempt` 计过图趟数，不移动。
- 取消从不重试。策略抛异常视为「不重试」。

## ExponentialBackoffRetry

**签名：** `sealed class ExponentialBackoffRetry : INodeRetryPolicy`

**构造函数：** `ExponentialBackoffRetry(int maxAttempts = 3, double baseDelayMs = 200, double factor = 2.0, double maxDelayMs = 5000)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `maxAttempts` | `int` | 含首次在内的总尝试次数；下限 `1`。 |
| `baseDelayMs` | `double` | 首次重试前等待；下限 `0`。 |
| `factor` | `double` | 每次等待的乘数；下限 `1`。 |
| `maxDelayMs` | `double` | 单次等待上限；下限 `baseDelayMs`。 |

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `MaxAttempts` | `int` | 配置的总次数。 |
| `NextRetryAsync(NodeFailure, CancellationToken)` | `Task<TimeSpan?>` | 返回 `baseDelay * factor^(RetryNumber-1)` 并受 `maxDelayMs` 限制；`RetryNumber >= MaxAttempts` 后返回 null。 |

延迟只是重试次数的纯函数；这里不检查异常。想「超时可重试、校验错误不重试」的宿主写自己的单方法实现即可。

## 示例

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RetryNode : IRedirectable
{
    public RetryNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }

    public Func<IRuntimeContext, INodeComponent?>? Redirect { get; set; }

    public Task<INodeComponent?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)
        => Task.FromResult(Redirect?.Invoke(context));
}

var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 10),
};
```
