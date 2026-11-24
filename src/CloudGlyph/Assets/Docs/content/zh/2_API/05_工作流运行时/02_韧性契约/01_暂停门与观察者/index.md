# 暂停门与观察者

运行可以在节点之间被按住，也可以作为时间线被观察。两项能力都不是必需的，也都不能改变运行走向。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## IExecutionGate

**签名：** `interface IExecutionGate`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WaitAsync(CancellationToken cancellationToken)` | `Task` | 每个节点前等待；按住返回的任务即可暂停。 |

门在节点**之间**暂停，绝不在节点内部：已在驱动的节点会跑完。取消必须抛出而不是返回，这样被停止的运行不会继续驱动。门按住期间 `IRuntimeContext.Status` 为 `Paused`，`IsRunning` 保持 `true`；释放后回到 `Running`。

## ManualExecutionGate

**签名：** `sealed class ManualExecutionGate : IExecutionGate`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `IsPaused` | `bool` | 运行是否被按住。 |
| `Pause()` | `void` | 在下一个节点边界按住；幂等。 |
| `Resume()` | `void` | 释放被按住的运行；未按住时无操作。 |
| `WaitAsync(CancellationToken)` | `Task` | 打开时返回已完成任务；否则等待，令牌触发时抛 `OperationCanceledException`。 |

`Pause` 与 `Resume` 可从任意线程安全调用，包括运行所在线程。门是一个仅在关闭期间存在的 `TaskCompletionSource`，在锁外完成。

## DelegateExecutionGate

**签名：** `sealed class DelegateExecutionGate(Func<CancellationToken, Task> wait) : IExecutionGate`

包装委托；null 抛 `ArgumentNullException`。`WaitAsync` 转发给它。

## ExecutionObservationKind

**签名：** `enum ExecutionObservationKind`

| 值 | 含义 |
| --- | --- |
| `RunStarted = 0` | 运行开始；`Node` 为 null。 |
| `BranchStarted` | 一个扇出分支开始；`Node` 为 null。 |
| `NodeStarted` | 节点即将驱动。 |
| `NodeSucceeded` | 节点未抛异常返回。 |
| `NodeFailed` | 节点抛出或报告错误。 |
| `NodeRetried` | 节点将再次驱动；重试次数在 `Detail`。 |
| `RunEnded` | 运行结束；`Node` 为 null。 |

## ExecutionObservation

**签名：** `readonly record struct ExecutionObservation(ExecutionObservationKind Kind, INodeComponent? Node, string? Detail, int Attempt, TimeSpan Elapsed)`

`Attempt` 是运行趟数，不是重试次数。`Detail` 是自由文本：失败消息、重试计数、分支标签。

## IExecutionObserver

**签名：** `interface IExecutionObserver`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `OnObservedAsync(ExecutionObservation observation, CancellationToken cancellationToken)` | `Task` | 每个观测调用一次；不得阻塞。 |

损坏的观察者从不改变运行：异常被记录，驱动继续。`RuntimeContext.Observer` 为 null 时不做任何观测。

## DelegateExecutionObserver

**签名：** `sealed class DelegateExecutionObserver(Action<ExecutionObservation> observe) : IExecutionObserver`

包装同步动作；null 抛 `ArgumentNullException`。

## IRuntimeAware

**签名：** `interface IRuntimeAware`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `AttachRuntimeContext(IRuntimeContext context)` | `void` | 每个节点驱动前立即收到会话。 |

同一个对象本来就是 `ReceiveAsync` 收到的参数，因此实现它不会损失什么，也不改变行为。只在节点需要在驱动之外拿到会话时使用，例如绑定进度。此处抛异常会被记录，驱动继续。

## 示例

```csharp
var gate = new ManualExecutionGate();
var observed = new List<ExecutionObservationKind>();
var session = new RuntimeContext
{
    Data = "seed",
    ExecutionGate = gate,
    Observer = new DelegateExecutionObserver(o => observed.Add(o.Kind)),
};

var run = new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
gate.Resume();   // 或在节点处理器内调用 Pause()
await run;

Console.WriteLine(session.Status);          // Completed
Console.WriteLine(string.Join(",", observed));
```
