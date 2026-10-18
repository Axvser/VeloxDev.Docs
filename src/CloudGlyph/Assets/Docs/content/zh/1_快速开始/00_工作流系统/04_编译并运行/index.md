# 工作流系统 — 正向编译（Root）并运行

编译入口是单个方法 `CompilerViewModel.CompileAsync(node, CompileRole role, ct)`。使用 `CompileRole.Root` 时，该节点是*起点*：编译器沿 `Targets` 向下游走，把可达子图分解成**一张**无环 `CompiledGraph`，同时存入 `CompilerViewModel.Graphs`。见 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs` 与 `CompileRole.cs`。

## 1. 从控制器节点正向编译

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.WorkflowSystem;

public static class Runner
{
    public static async Task RunForwardAsync(QuickTree tree)
    {
        var ticker = tree.Nodes.OfType<TickerNode>().Single();
        var bias = tree.Nodes.OfType<BiasNode>().Single();
        var printer = tree.Nodes.OfType<PrinterNode>().Single();

        var compiler = new CompilerViewModel();
        IReadOnlyList<CompiledGraph> graphs =
            await compiler.CompileAsync(ticker, CompileRole.Root, CancellationToken.None);
        CompiledGraph graph = graphs[0];
    }
}
```

`CompileAsync` 要求传入 `IWorkflowNodeViewModel`（否则抛 `ArgumentException`），返回 `IReadOnlyList<CompiledGraph>`；`compiler.Graphs` 镜像同一结果，供 UI 绑定。

**预期结果：** `graph.Entries.Count == 1` —— 线性 `Ticker → Bias → Printer` 链编译成单个分段。每个实现 `ICompileTimeAware` 的节点都被注入编译身份：`ticker.CompileContext!.Order == 0`、`bias.CompileContext!.Order == 1`、`printer.CompileContext!.Order == 2`。

## 2. `CompiledGraph` 由什么组成

`CompiledGraph.Entries` 是有序的 `ObservableCollection<CompileSegment>`。三个具体分段（`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Model/`）是：

| 分段 | 含义 | 何时产生 |
|---|---|---|
| `ChainSegment` | 有序的线性节点序列 | 单入 / 单出的直线（本例 `Ticker → Bias → Printer`） |
| `BranchSegment` | 一个路由节点 + 它的 `BranchOption` | 实现 `ICompileTimeRouter` 的节点 |
| `ParallelSegment` | 由子 `CompiledGraph` 组成的扇出组 | 一个路由键 / 普通输出喂给多个下游目标，或多个生产者汇入一个节点 |

路由器（`ICompileTimeRouter`）在编译期用 `GetRouteTable()`（键 → 下游节点）声明分支结构，运行期用 `ResolveRouteKey(payload)` 重新选择；`RouterCompileMode.Static` 把当前选中的分支锁进图，`RouterCompileMode.Dynamic` 保留所有分支。分支分段嵌套子图，所以编译图是一棵分段树。图是无环且不可变的 —— 它*描述*可能的执行；实际走哪条分支在运行期决定。

**预期结果：** 对这条线性图，`graph.Entries[0] is ChainSegment`，其 `Nodes` 按顺序持有三个节点实例。

## 3. 运行编译图

```csharp
var context = new RuntimeContext();
await new RuntimeEngine().RunAsync(graph, context, CancellationToken.None);

Console.WriteLine(context.Status);        // Completed
Console.WriteLine(context.Data);          // tick->bias->print
foreach (var line in context.Logs) Console.WriteLine(line);
```

`RuntimeEngine`（`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`）驱动每个分段：`ChainSegment` 逐个驱动节点，`BranchSegment` 驱动路由器再驱动选中的子图，`ParallelSegment` 并发运行各分支（交错的异步工作，不是线程并行）。每个节点通过 Helper 的 `ReceiveAsync` 用**同一个** `RuntimeContext` 会话驱动（实现 `IRuntimeAware` 的节点也会被注入该会话）。节点返回值写回 `context.Data`，所以链上下一个节点收到上一个节点的输出 —— 这正是 `Bias` 看到 `"tick"`、`Printer` 看到 `"tick->bias"` 的原因。

**预期结果：** `context.Status == "Completed"`、`context.Data == "tick->bias->print"`、`context.Attempt == 1`，且 `RunAsync` 返回时 `context.IsRunning` 为 `false`。取消令牌（或不可重定向的节点错误）则得到 `Status == "Stopped"`。

读取 `Outcome`，而不是解析 `Status`：它是对 `Status` + `EndedWithError` 的精确解读，因为 `"Stopped"` 这一个词要同时覆盖失败与取消。

```csharp
Console.WriteLine($"{context.Status} {context.Outcome}");   // Completed Completed
```

| `Outcome` | 何时 |
|---|---|
| `Unknown` | 运行尚未结束 —— 从未开始，或仍在运行 |
| `Completed` | 每个入口都被走过（提前结束运行的终端分支也算完成） |
| `Cancelled` | `Status == "Stopped"` 且 `EndedWithError == false` —— 宿主的令牌结束了它 |
| `Failed` | `Status == "Stopped"` 且 `EndedWithError == true` —— 失败结束了流程 |

**预期结果：** 本图为 `Completed Completed`。

编译图还可以压平成一份可绑定的列表，适合树视图：

```csharp
foreach (var row in CompiledOutline.Of(graph))
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind} | {row.Label}");
```

**预期结果：** `Execute | TickerNode → BiasNode → PrinterNode` —— 只有一行，因为线性链就是一个 `ChainSegment`。每行携带 `Depth`、`Kind`（`Execute` / `Branch` / `Parallel`）、`Label` 与它命名的节点。

## 4. 三个执行入口

编译运行只是三种执行方式之一（见 `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/` 的 `EntrySemanticsTests`）。

**节点级。** 直接调用节点的接收路径：

```csharp
var result = await ticker.GetHelper().ReceiveAsync(
    new TaskContext("hello"), CancellationToken.None);
```

`TaskContext`（`Src/Core/VeloxDev.Core/WorkflowSystem/TaskContext.cs`）是只读的 `ITaskContext` 载体 `(Data, Sender, Receiver)`。

**边级。** 沿每条有效出边广播负载；每条通过的边把 `TaskContext` 投递给下游节点的 `ReceiveCommand`（`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs`）：

```csharp
using VeloxDev.WorkflowSystem.StandardEx;
await ticker.StandardBroadcastAsync("hello", CancellationToken.None);
```

`AccessAsync` 拒绝负载的边被视为未连接并跳过。

**链级（编译）。** 第 3 步的引擎负责下游派发：它只通过 `Helper.ReceiveAsync` 驱动节点，绝不触发节点的 `ReceiveCommand` / `BroadcastCommand`。

前往「编译结果（Terminal）」。
