# Root compilation

Compiling from the root walks downstream from one start node and produces a graph whose entries are chains, branches and fan-out groups. This page builds a diamond — one source, two parallel workers, one join — and reads the resulting segments, compile orders and flat outline.

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- The four component roles declared as in [Workflow graph model](../../00_workflow-graph-model/index.md).

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Build a graph that decomposes

A source slot that feeds two workers must accept multiple targets; a join input that receives two workers must accept multiple sources. With the wrong channel, the second connection replaces the first and the graph silently loses a branch.

```csharp
source.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
join.Input.SetChannelCommand.Execute(SlotChannel.MultipleSources);

Wire(tree, source.Output, a.Input);
Wire(tree, source.Output, b.Input);
Wire(tree, a.Output, join.Input);
Wire(tree, b.Output, join.Input);
```

**Expected result:** `source.Output.Targets.Count == 2` and `join.Input.Sources.Count == 2`.

## 4. Compile from the root

```csharp
var compiler = new CompilerViewModel();
var graphs = await compiler.CompileAsync(source, CompileRole.Root);
var graph = graphs[0];
```

`CompileAsync` requires an `INodeComponent` for the start node; it clears `compiler.Graphs` and returns the graphs produced by this call. The call is asynchronous because a router's route table and each edge's `AccessAsync` check are asynchronous.

**Expected result:** `graphs.Count == 1`, and `graph.Entries` has three entries: `ChainSegment` (source), `ParallelSegment` (two branches), `ChainSegment` (join).

## 5. Read segments, orders and the outline

Each compiled node has an identity in the graph's binding table — `Order`, `ChainIndex`, `Offset`, and the join inputs if any. Read it from the **graph**, not from the node.

```csharp
static string OrderOf(CompiledGraph graph, INodeComponent node)
    => graph.TryGetCompileInfo(node, out var info) ? info!.Order.ToString() : "-";

Console.WriteLine($"orders: source={OrderOf(graph, source)} a={OrderOf(graph, a)} b={OrderOf(graph, b)} join={OrderOf(graph, join)}");
```

**Expected result:** `source=0 a=1 b=2 join=3`. The order is global and strictly increasing in drive order, including across fan-out branches.

For a flat, bindable view of the same graph, use `CompiledOutline.Of`:

```csharp
foreach (var row in CompiledOutline.Of(graph))
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Depth} {row.Kind}: {row.Label}");
```

**Expected result:** one row for the source chain, one `Parallel: 2 branches` row with two indented `Execute` rows, and one row for the join chain.

`CompiledOutlineRow.Kind` is `Execute`, `Branch`, `Parallel`, `Option` or `Terminal`; the label names the node types in the chain, or the router and its keys.

## 6. Optional node notifications

The authoritative compile identity lives in `CompiledGraph.CompileBindings`. A node implementing `ICompileTimeAware` also receives a **copy** through `AttachCompileTimeContext`, which is useful for a compile badge — but the runtime never reads that copy back, and a node that implements nothing still takes part in joins and redirects.

The compiler also asks each node's helper `AccessAsync` before following an output edge. Returning `false` treats the edge as unconnected: it is left out of the compiled graph, exactly as it would be left out of a runtime broadcast. A compile-order `-1` appears only when a static router prunes a branch; see [Branches and terminal compilation](../01_branches-and-terminal/index.md).

## 7. Verification

```powershell
dotnet run
```

Expected output:

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

## 8. Complete code

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

## 9. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
