# 根节点编译

从根编译会从某个起始节点向下游走，产出的图由链、分支和扇出组构成。本页搭一个菱形——一个源、两个并行工作者、一个汇合点——并读取产出的段、编译序号与扁平大纲。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 四种组件角色按[工作流图模型](../../00_工作流图模型/index.md)声明。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 搭一张能分解的图

一个向两个工作者发送的源插槽必须接受多个目标；一个接收两个工作者的汇合输入必须接受多个来源。通道设错时，第二次连线会替换第一次，图会悄悄丢掉一条分支。

```csharp
source.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
join.Input.SetChannelCommand.Execute(SlotChannel.MultipleSources);

Wire(tree, source.Output, a.Input);
Wire(tree, source.Output, b.Input);
Wire(tree, a.Output, join.Input);
Wire(tree, b.Output, join.Input);
```

**预期结果：** `source.Output.Targets.Count == 2`，`join.Input.Sources.Count == 2`。

## 4. 从根节点编译

```csharp
var compiler = new CompilerViewModel();
var graphs = await compiler.CompileAsync(source, CompileRole.Root);
var graph = graphs[0];
```

`CompileAsync` 的起始节点必须是 `INodeComponent`；它会清空 `compiler.Graphs` 并返回本次调用产生的图。调用是异步的，因为路由器的路由表和每条边的 `AccessAsync` 检查都是异步的。

**预期结果：** `graphs.Count == 1`，`graph.Entries` 有三项：`ChainSegment`（源）、`ParallelSegment`（两条分支）、`ChainSegment`（汇合）。

## 5. 读取段、序号与大纲

每个被编译的节点在图自己的绑定表里有一个身份——`Order`、`ChainIndex`、`Offset`，以及汇合节点的输入源。请从**图**上读取，而不是从节点上读。

```csharp
static string OrderOf(CompiledGraph graph, INodeComponent node)
    => graph.TryGetCompileInfo(node, out var info) ? info!.Order.ToString() : "-";

Console.WriteLine($"orders: source={OrderOf(graph, source)} a={OrderOf(graph, a)} b={OrderOf(graph, b)} join={OrderOf(graph, join)}");
```

**预期结果：** `source=0 a=1 b=2 join=3`。序号是全局的，并按驱动顺序严格递增，跨扇出分支也成立。

要得到可绑定的扁平视图，使用 `CompiledOutline.Of`：

```csharp
foreach (var row in CompiledOutline.Of(graph))
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Depth} {row.Kind}: {row.Label}");
```

**预期结果：** 一行源链、一行带两条缩进 `Execute` 的 `Parallel: 2 branches`，以及一行汇合链。

`CompiledOutlineRow.Kind` 为 `Execute`、`Branch`、`Parallel`、`Option` 或 `Terminal`；标签给出链中的节点类型，或路由器及其键。

## 6. 可选的节点通知

权威的编译身份存放在 `CompiledGraph.CompileBindings`。实现 `ICompileTimeAware` 的节点还会通过 `AttachCompileTimeContext` 收到一份**副本**，适合显示编译徽标——但运行期从不读回这份副本，完全不实现任何接口的节点同样参与汇合与重定向。

编译器在沿输出边前进前还会询问节点 Helper 的 `AccessAsync`。返回 `false` 表示该边视为未连接：它不会进入编译图，与运行期广播时被跳过的语义一致。编译序号 `-1` 只在静态路由器剪掉分支时出现，见[分支与终止编译](../01_分支与终止编译/index.md)。

## 7. 验证

```powershell
dotnet run
```

预期输出：

```text
entries=3: ChainSegment,ParallelSegment,ChainSegment
outline:
0 Execute: StepNode
0 Parallel: 2 branches
  1 Execute: StepNode
  1 Execute: StepNode
0 Execute: StepNode
orders: source=0 a=1 b=2 join=3
```

## 8. 完整代码

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Compiler.Root;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class StepNode
{
    public StepNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Step";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

public static class Program
{
    private static void Wire(DemoTree tree, ISlotComponent from, ISlotComponent to)
    {
        tree.GetHelper().SendConnection(from);
        tree.GetHelper().ReceiveConnection(to);
    }

    private static string OrderOf(CompiledGraph graph, INodeComponent node)
        => graph.TryGetCompileInfo(node, out var info) ? info!.Order.ToString() : "-";

    public static async Task Main()
    {
        var tree = new DemoTree();
        var source = new StepNode("source");
        var a = new StepNode("a");
        var b = new StepNode("b");
        var join = new StepNode("join");
        foreach (var n in new INodeComponent[] { source, a, b, join }) tree.GetHelper().CreateNode(n);

        source.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
        join.Input.SetChannelCommand.Execute(SlotChannel.MultipleSources);
        Wire(tree, source.Output, a.Input);
        Wire(tree, source.Output, b.Input);
        Wire(tree, a.Output, join.Input);
        Wire(tree, b.Output, join.Input);

        var compiler = new CompilerViewModel();
        var graphs = await compiler.CompileAsync(source, CompileRole.Root);
        var graph = graphs[0];

        Console.WriteLine($"entries={graph.Entries.Count}: {string.Join(",", graph.Entries.Select(e => e.GetType().Name))}");
        Console.WriteLine("outline:");
        foreach (var row in CompiledOutline.Of(graph))
            Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Depth} {row.Kind}: {row.Label}");

        Console.WriteLine($"orders: source={OrderOf(graph, source)} a={OrderOf(graph, a)} b={OrderOf(graph, b)} join={OrderOf(graph, join)}");
    }
}
```

## 9. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
