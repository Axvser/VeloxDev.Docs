# 工作流系统 — 执行契约

宿主接入编译运行的七个可选接缝，以及它们的载荷类型。这里每个契约都从宿主具体的 `RuntimeContext` 上读；一个都不配置时，运行的表现与它们存在之前一模一样（见`运行时上下文 — 宿主能力`）。

源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Contracts/` —— `IExecutionGate.cs`、`IExecutionObserver.cs`、`INodeRetryPolicy.cs`、`IExecutionErrorSink.cs`、`IExecutionCompensation.cs`、`IExecutionCheckpointStore.cs`、`ILogWriter.cs`。

## 七个接缝

| 契约 | 会话属性 | 一句话 |
|---|---|---|
| `IExecutionGate` | `ExecutionGate` | 在节点之间暂停运行。 |
| `IExecutionObserver` | `Observer` | 按顺序观察运行做了什么。 |
| `INodeRetryPolicy` | `RetryPolicy` | 决定抛出异常的节点能不能再来一次。 |
| `IExecutionErrorSink` | `ErrorSink` | 把失败作为记录而非日志行收到。 |
| `IExecutionCompensation` | `Compensation` | 把收尾不佳的运行的成果交还宿主。 |
| `IExecutionCheckpointStore` | `CheckpointStore` | 写下运行的位置，让后来的运行接手。 |
| `ILogWriter` | `LogWriter` | 把运行的行导到内存之外。 |

本页讲前两个，其余各有专页：

- `重试与错误接收器` —— `INodeRetryPolicy`、`NodeFailure`、`IExecutionErrorSink`、`ExecutionError`、`ExecutionFailurePhase`、`ExecutionReportLevel`
- `补偿、检查点与日志` —— `IExecutionCompensation`、`NodeCompensation`、`IExecutionCheckpointStore`、`ILogWriter`、`LogWriteFailedEventArgs`

---

## `IExecutionGate`

编译运行的暂停点。`RuntimeEngine` 在每个节点驱动前等待它，因此宿主可以握住一轮长运行，然后再放开。

#### `IExecutionGate.WaitAsync`

**签名：** `Task WaitAsync(CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `cancellationToken` | `CancellationToken` | 运行的令牌。**必须**被遵守。 |

**返回：** `Task` —— 返回已完成的任务即放行；握住返回的 Task 即暂停。同一个门会在下一个节点前再被问一次，所以放开它就恢复了运行。

**异常：**

| 异常 | 条件 |
|---|---|
| `OperationCanceledException` | 取消时**必须**抛出。`RuntimeEngine.RunAsync` 会把它转成 `Status = "Stopped"`。 |

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
Gate.Resume();                          // 一次运行绝不带着上一次留下的暂停开始
context.ExecutionGate = Gate;           // Gate 是一个 ManualExecutionGate
```

**说明：**

- **它只在节点之间暂停，绝不在节点内部暂停。** 已经在被驱动的节点会跑完 —— 与工具层对「半个变更不允许中途丢弃」是同一条规矩，也是暂停不会破坏图的原因。
- **取消必须*抛出*而不是返回。** 取消时正常返回会让调用方继续循环，而「宿主停掉一个正在暂停的运行」必须结束而不是挂住。
- 门握住期间，引擎写 `Status = "Paused"`，放开时写回 `"Running"` —— 一个暂停中的运行没有别的可绑定状态，因为 `IsRunning` 只区分「在跑」与「不在跑」。开着的门不花代价：引擎先看 `IsCompleted`，连 `Status` 都不写。
- 在扇出内部，门是经分支门面取到的，所以它同样能握住各分支（`ExecutionGateTests.AClosedGate_AlsoHoldsTheBranchesOfAFanOut`）。

---

## `IExecutionObserver`

观察一次编译运行：谁被驱动了、按什么顺序、结果如何。挂 OpenTelemetry（或任何想要运行时间线的东西）的接缝。

#### `IExecutionObserver.OnObservedAsync`

**签名：** `Task OnObservedAsync(ExecutionObservation observation, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `observation` | `ExecutionObservation` | 发生了什么：种类、节点、细节、趟号、耗时。 |
| `cancellationToken` | `CancellationToken` | 运行的令牌。 |

**返回：** `Task`。不得阻塞 —— 运行正在等它。

**异常：** 没有任何能到达运行的异常。**坏掉的观察者绝不改变运行**：抛出的异常被吞掉并写进运行自己的日志（`[Observer] {kind} was not observed: {message}`），因为观察是诊断而不是证据。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.Observer = new DelegateExecutionObserver(Observe);

// 只写汇总，且在 RunEnded 时写 —— 一轮跑二十来个节点，逐条写会把日志本身淹掉。
private void Observe(ExecutionObservation observation)
{
    switch (observation.Kind)
    {
        case ExecutionObservationKind.NodeStarted:
            _nodesDriven++;
            break;
        case ExecutionObservationKind.NodeRetried:
            _retries++;
            break;
        case ExecutionObservationKind.RunEnded:
            var outcome = (Controller.RuntimeContext as RuntimeContext)?.Outcome;
            Controller.RuntimeContext?.Log(
                $"[Observer] {_nodesDriven} nodes driven, {_retries} retried, pass {observation.Attempt}, " +
                $"{observation.Elapsed.TotalSeconds:0.0}s, {outcome}");
            _nodesDriven = 0;
            _retries = 0;
            break;
    }
}
```

### `ExecutionObservationKind`

**签名：** `public enum ExecutionObservationKind`

| 成员 | 值 | `Observation.Node` |
|---|---|---|
| `RunStarted` | 0 | `null` |
| `BranchStarted` | 1 | `null`；细节里带 `"branch {index}"` |
| `NodeStarted` | 2 | 即将被驱动的节点 |
| `NodeSucceeded` | 3 | 未抛异常返回的节点 |
| `NodeFailed` | 4 | 抛出异常或请求重定向的节点；细节里带消息 |
| `NodeRetried` | 5 | 正在被再次驱动的节点；细节里带重试序号 |
| `RunEnded` | 6 | `null`；耗时是整轮的 |

### `ExecutionObservation`

**签名：**

```csharp
public readonly record struct ExecutionObservation(
    ExecutionObservationKind Kind,
    IWorkflowNodeViewModel? Node,
    string? Detail,
    int Attempt,
    TimeSpan Elapsed);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `Kind` | `ExecutionObservationKind` | 发生了什么。 |
| `Node` | `IWorkflowNodeViewModel?` | 本条关于的节点；运行级或分支级观察为 `null`。 |
| `Detail` | `string?` | 自由文本上下文：失败消息、重试计数、分支键。 |
| `Attempt` | `int` | 运行的趟号 —— 这是第几趟过图。重试**不是**新的一趟，不会推进它。 |
| `Elapsed` | `TimeSpan` | 该步骤花了多久（在有意义的地方）。 |

**说明：** 一个形状带一个种类 —— 而不是每种一个方法 —— 这样新增一种不会破坏既有的观察者；这也正是本库中运行自身的各事件已经在用的形状。

**线性链上的观察顺序（测试）：**

```text
RunStarted, NodeStarted, NodeSucceeded, NodeStarted, NodeSucceeded, RunEnded
```

`CompilerEx/ExecutionObserverTests.cs` —— `AChain_ReportsRunAndNodeStartAndSuccess_InDriveOrder`；`AFanOut_ReportsEveryBranch` 数出两次 `BranchStarted` 与三次 `NodeStarted`（源加上两条分支节点）；`AThrowingObserver_ChangesNothingAboutTheRun` 钉住抛异常的观察者会让 `Status == "Completed"`。

## 子页

| 页面 | 内容 |
|---|---|
| [重试策略与错误接收器](01_重试与错误接收器/index.md) | `INodeRetryPolicy`、`NodeFailure`、`IExecutionErrorSink`、`ExecutionError`、`ExecutionFailurePhase`、`ExecutionReportLevel` |
| [补偿、检查点与日志写入器](02_补偿检查点与日志/index.md) | `IExecutionCompensation`、`NodeCompensation`、`IExecutionCheckpointStore`、`ILogWriter`、`LogWriteFailedEventArgs` |
