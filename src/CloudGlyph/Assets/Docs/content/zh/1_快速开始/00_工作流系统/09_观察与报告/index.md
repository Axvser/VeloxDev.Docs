# 工作流系统 — 观察运行并读取结果

观察一次运行有两种方式：`IExecutionObserver` 拿到时间线，`RunOutcome` 给 `Status` 一个精确解读。两者都在「安装与创建项目」创建的会话上。

## 1. 观察时间线

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var observed = new List<string>();
var context = new RuntimeContext
{
    Observer = new DelegateExecutionObserver(o =>
    {
        if (o.Kind is ExecutionObservationKind.NodeStarted or ExecutionObservationKind.NodeSucceeded)
            observed.Add($"{o.Kind}:{o.Node?.GetType().Name}");
    }),
};

await new RuntimeEngine().RunAsync(rootGraph, context, CancellationToken.None);
Console.WriteLine(string.Join(", ", observed));
```

**预期结果：** 每个节点一对记录，按驱动顺序：

```text
NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
```

**说明：** 三个运行/分支级种类（`RunStarted`、`BranchStarted`、`RunEnded`）的 `Node == null`；每条观察还携带 `Attempt`（属于哪一趟）与 `Elapsed`（该步耗时）。`ExecutionObservationKind` 有七个成员 —— `RunStarted`、`BranchStarted`、`NodeStarted`、`NodeSucceeded`、`NodeFailed`、`NodeRetried`、`RunEnded`。抛异常的观察者会被吞掉并记入日志（`[Observer] …`）：观察是诊断，不是证据。

## 2. 把失败报告成记录

`IExecutionErrorSink` 接收运行记录的每一次失败，作为结构化数据而不是日志行：

```csharp
var records = new List<ExecutionError>();
var sinkContext = new RuntimeContext
{
    ErrorSink = new DelegateExecutionErrorSink(records.Add),
};

await new RuntimeEngine().RunAsync(rootGraph, sinkContext, CancellationToken.None);
Console.WriteLine($"records on a clean run: {records.Count}");
```

**预期结果：** `records on a clean run: 0` —— 什么都没失败，所以什么都没报告。

节点也可以通过异步方式报告，同样进入 sink：

```csharp
// inside a NodeHelper<T>.ReceiveAsync override
public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
{
    if (context is IRuntimeContext rc && rc.Attempt == 2)
        await rc.ErrorAsync("the interpreter died");     // writes [Error] and records it
    else if (context is IRuntimeContext rc2)
        await rc2.WarnAsync("nothing to run");          // writes [Warning] and records it
    return context.Data;
}
```

**预期结果：** 警告记录一条 `Level == Warning`，运行带着节点自己的返回值继续；错误记录一条 `Level == Error`，并且 —— 除非节点实现 `IRedirectable` —— 以 `Status == "Stopped"`、`CurrentOrder == -1` 结束流程。同步的 `Error` / `Warn` 按设计只写日志行：它们在节点的栈帧里运行，绝不能阻塞。

## 3. 读取结果

`Status` 不得不用 `"Stopped"` 一个词同时表示失败与取消，所以请读 `Outcome`：

```csharp
var completed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, completed, CancellationToken.None);
Console.WriteLine($"{completed.Status} {completed.Outcome}");     // Completed Completed
```

**预期结果：** `Completed Completed`。映射如下：

| `Outcome` | 何时 |
|---|---|
| `Unknown` | 运行尚未结束 —— 从未开始，或仍在运行 |
| `Completed` | `Status == "Completed"` —— 每个入口都被走过（提前结束运行的终端分支也算完成） |
| `Cancelled` | `Status == "Stopped"` 且 `EndedWithError == false` —— 宿主令牌结束了它 |
| `Failed` | `Status == "Stopped"` 且 `EndedWithError == true` —— 失败结束了流程 |

**说明：** 被取消的运行刻意**不写** `[Error]` 日志行 —— 宿主停止自己的运行不是失败，写了反而会让之后读 `Logs` 的人以为发生过失败。它仍会向 sink 报告一条 `Run` 阶段记录，`Node == null`。

## 4. 真实仓库中的位置

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 在 `ConfigureRun` 中设置两者：`context.Observer = new DelegateExecutionObserver(Observe);` 与 `context.ErrorSink = new DelegateExecutionErrorSink(Diagnostics.Add);`（`Diagnostics` 是 `ObservableCollection<ExecutionError>`）。它的 `Observe` 统计 `NodeStarted` / `NodeRetried`，并在 `RunEnded` 写**一条**摘要行 —— 一次运行驱动二十多个节点，逐个写会淹没日志：

```text
[Observer] {nodes} nodes driven, {retries} retried, pass {attempt}, {seconds}s, {outcome}
```

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionObserverTests.cs` 与 `ExecutionErrorSinkTests.cs`（后者钉住节点抛异常、节点报告、路由器抛异常、重定向解析抛异常、宿主取消与重定向上限各自记录的阶段）。

前往「重试与补偿」。
