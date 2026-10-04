# Workflow System — 观察一次运行并读取它的结局

看一次运行有两种方式：`IExecutionObserver` 拿到它的时间线，`RunOutcome` 给 `Status` 一个精确读法。两者都挂在 `01_安装` 建好的那个会话上。

## 1. 看时间线

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

**预期结果：** 每个节点一对，按驱动顺序：

```text
NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
```

**说明：** 运行级与分支级的三种观察（`RunStarted`、`BranchStarted`、`RunEnded`）`Node == null`；每条观察还带 `Attempt`（属于哪一趟）与 `Elapsed`（该步骤花了多久）。`ExecutionObservationKind` 有七个成员 —— `RunStarted`、`BranchStarted`、`NodeStarted`、`NodeSucceeded`、`NodeFailed`、`NodeRetried`、`RunEnded`。抛异常的观察者会被吞掉并记一行日志（`[Observer] …`）：观察是诊断，不是证据。

## 2. 把失败当作记录上报

`IExecutionErrorSink` 收到运行记录的每一次失败，形态是结构化数据而不是日志行：

```csharp
var records = new List<ExecutionError>();
var sinkContext = new RuntimeContext
{
    ErrorSink = new DelegateExecutionErrorSink(records.Add),
};

await new RuntimeEngine().RunAsync(rootGraph, sinkContext, CancellationToken.None);
Console.WriteLine($"records on a clean run: {records.Count}");
```

**预期结果：** `records on a clean run: 0` —— 什么都没失败，所以什么都没上报。

节点也可以通过异步那一对上报告，它会同时喂给接收器：

```csharp
// 在 NodeHelper<T>.ReceiveAsync 的重写里
public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
{
    if (context is IRuntimeContext rc && rc.Attempt == 2)
        await rc.ErrorAsync("the interpreter died");     // 写 [Error] 并记录
    else if (context is IRuntimeContext rc2)
        await rc2.WarnAsync("nothing to run");          // 写 [Warning] 并记录
    return context.Data;
}
```

**预期结果：** 警告记一条 `Level == Warning` 的登记，并让运行带着节点自己的返回值继续；错误记一条 `Level == Error` 的登记，并且 —— 除非节点实现了 `IRedirectable` —— 以 `Status == "Stopped"`、`CurrentOrder == -1` 结束流程。同步的 `Error` / `Warn` 只写日志行，这是刻意的：它们跑在节点帧里，绝不能阻塞。

## 3. 读结局

`Status` 必须让一个 `"Stopped"` 同时承担失败与取消，所以改读 `Outcome`：

```csharp
var completed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, completed, CancellationToken.None);
Console.WriteLine($"{completed.Status} {completed.Outcome}");     // Completed Completed
```

**预期结果：** `Completed Completed`。映射如下：

| `Outcome` | 何时 |
|---|---|
| `Unknown` | 运行还没结束 —— 没跑过，或还在跑 |
| `Completed` | `Status == "Completed"` —— 每个条目都走完了（合法地提前结束整轮的终结分支也算完成） |
| `Cancelled` | `Status == "Stopped"` 且 `EndedWithError == false` —— 宿主的令牌结束了它 |
| `Failed` | `Status == "Stopped"` 且 `EndedWithError == true` —— 失败让流程提前结束 |

**说明：** 被取消的运行刻意**不**写 `[Error]` 日志行 —— 宿主停掉自己的运行不是失败，加一行 `[Error]` 会让以后读 `Logs` 的人以为出过错。它仍会向接收器报一条 `Run` 相位、`Node == null` 的记录。

## 4. 真实仓库里它在哪

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 在 `ConfigureRun` 里设置了两者：`context.Observer = new DelegateExecutionObserver(Observe);` 与 `context.ErrorSink = new DelegateExecutionErrorSink(Diagnostics.Add);`（`Diagnostics` 是 `ObservableCollection<ExecutionError>`）。它的 `Observe` 数 `NodeStarted` / `NodeRetried`，只在 `RunEnded` 时写**一行**汇总 —— 一轮跑二十来个节点，逐条写会把日志本身淹掉：

```text
[Observer] {nodes} nodes driven, {retries} retried, pass {attempt}, {seconds}s, {outcome}
```

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionObserverTests.cs` 与 `ExecutionErrorSinkTests.cs`（后者钉住了节点抛出、节点上报、路由器抛出、重定向解析抛出、宿主取消、超重定向上限各场景的记录相位）。

下一步见 `10_重试与补偿`。
