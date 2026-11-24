# Branches and terminal compilation

A router turns the graph into a `BranchSegment`: `GetRouteTable` declares key → downstream nodes, and `ResolveRouteKey` decides which key a run takes. The same contract supports a compile-time decision (static) and a run-time one (dynamic). Compiling from a terminal walks the other way and keeps only the ancestor cone needed for one node.

This page continues from [Root compilation](../00_root-compilation/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- The graph and component declarations from the root-compilation page.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Declare a router

A router is an ordinary node that implements `ICompileTimeRouter`. Its branch ports come from the same `SlotEnumerator<TSlot>` used in [Dynamic slot enumeration](../../03_dynamic-slot-enumeration/index.md).

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter
{
    public RouterNode(string title) { Title = title; InitializeWorkflow(); }

    [VeloxProperty] public partial SlotViewModel Input { get; set; }

    [VeloxProperty]
    [SlotSelectors(typeof(RouteKey))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public RouterCompileMode Mode { get; set; } = RouterCompileMode.Dynamic;
    public object? Selection { get; set; } = RouteKey.A;
    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(Mode == RouterCompileMode.Dynamic && payload is null ? null : Selection);

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Mode == RouterCompileMode.Static && Selection is not null && Routes.TryGetValue(Selection, out var only)
                ? new Dictionary<object, IReadOnlyList<INodeComponent>> { [Selection] = only }
                : Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }
}
```

`RouterCompileMode` is this sample's own policy. `ICompileTimeRouter` only asks two questions, and a router is free to answer them from whatever state it has.

**Expected result:** the router compiles into a `BranchSegment` when it is reachable, with one `BranchOption` per route key.

## 4. Route table and route key

- `GetRouteTable()` is called at compile time. An entry whose node list is empty is a **terminal option**: choosing it at run time ends the run.
- `ResolveRouteKey(payload)` is called at compile time with `null`, and at run time with the session. Returning `null` for the compile-time call means "undecidable now" → the branch is **dynamic** and every option stays in the graph. Returning a key means **static** and that key is locked as `CompileKey`.

```csharp
router.OutputSlots.SetSelector(typeof(RouteKey));
router.Routes[RouteKey.A] = [x];
router.Routes[RouteKey.B] = [y];
if (router.OutputSlots.TrySelect(RouteKey.A, out var slotA)) Wire(tree, slotA!, x.Input);
if (router.OutputSlots.TrySelect(RouteKey.B, out var slotB)) Wire(tree, slotB!, y.Input);
```

**Expected result:** each branch slot is connected to its worker, so the topology and the route table agree.

## 5. Static pruning versus dynamic branches

```csharp
var dynamicGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
var dynamicBranch = (BranchSegment)dynamicGraph.Entries[1];
// options=2, IsDynamic=True, CompileKey=null

router.Mode = RouterCompileMode.Static;
router.Selection = RouteKey.A;
var staticGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
var staticBranch = (BranchSegment)staticGraph.Entries[1];
// options=1, IsDynamic=False, CompileKey=A
```

In static mode the unselected branch is not merely skipped at run time: its downstream nodes are visited and given `Order = -1` (the absolute stop state), and they appear in no segment. `graph.TryGetCompileInfo(y, out _)` still returns `true` with `Order == -1`; `CompiledOutline` does not list it.

**Expected result:** dynamic reports two options and `x=2, y=3`; static reports one option, `x=2, y=-1`.

## 6. Fan-out inside a route key

If a route key maps to several downstream nodes, the compiler recurses into each and wraps them in a `ParallelSegment` inside that option's subgraph. The node all branch exits point to becomes the join point and the start of the next chain in the parent graph. A plain (non-router) node with several valid targets decomposes the same way.

## 7. Terminal compilation

`CompileRole.Terminal` takes the node whose result you want, walks `Sources` to collect its ancestor cone, derives the cone's own entry frontier, and compiles only what is needed to compute that node.

```csharp
var cone = (await compiler.CompileAsync(y, CompileRole.Terminal))[0];
```

Under a cone, sibling branches are **absent**, not stopped: `x` has no compile binding at all. If the router has more than one branch that can reach the target, the cone is refused with an `InvalidOperationException` — a single forward run can only take one branch, so a result that needs two is not fabricated.

At run time, set `RuntimeContext.Target` to the terminal node. `TargetReached` becomes `true` only if that node was actually driven. With the dynamic router above, the cone keeps the branch that reaches `y`, but the run still has to choose that key.

```csharp
router.Selection = RouteKey.B;
var session = new RuntimeContext { Data = "seed", Target = y };
await new RuntimeEngine().RunAsync(cone, session, CancellationToken.None);
```

**Expected result:** `status=Completed`, `targetReached=True`.

## 8. Verification

```powershell
dotnet run
```

Expected output:

```text
[dynamic] options=2 isDynamic=True key=null
[dynamic] x=2 y=3
[static] options=1 isDynamic=False key=A
[static] x=2 y=-1
[terminal] entries=ChainSegment,BranchSegment
[terminal] x=- y=2; containsSource=True
[terminal] status=Completed targetReached=True depth=4
```

## 9. Complete code

```csharp
using VeloxDev.AI;
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Compiler.Branches;

public enum RouteKey { A, B }

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

[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter
{
    public RouterNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Router";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty]
    [SlotSelectors(typeof(RouteKey))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public RouterCompileMode Mode { get; set; } = RouterCompileMode.Dynamic;
    public object? Selection { get; set; } = RouteKey.A;
    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(Mode == RouterCompileMode.Dynamic && payload is null ? null : Selection);

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Mode == RouterCompileMode.Static && Selection is not null && Routes.TryGetValue(Selection, out var only)
                ? new Dictionary<object, IReadOnlyList<INodeComponent>> { [Selection] = only }
                : Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }
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
        var router = new RouterNode("router");
        var x = new StepNode("x");
        var y = new StepNode("y");
        foreach (var n in new INodeComponent[] { source, router, x, y }) tree.GetHelper().CreateNode(n);
        Wire(tree, source.Output, router.Input);

        router.OutputSlots.SetSelector(typeof(RouteKey));
        router.Routes[RouteKey.A] = [x];
        router.Routes[RouteKey.B] = [y];
        if (router.OutputSlots.TrySelect(RouteKey.A, out var slotA)) Wire(tree, slotA!, x.Input);
        if (router.OutputSlots.TrySelect(RouteKey.B, out var slotB)) Wire(tree, slotB!, y.Input);

        var compiler = new CompilerViewModel();

        var dynamicGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
        var dynamicBranch = (BranchSegment)dynamicGraph.Entries[1];
        Console.WriteLine($"[dynamic] options={dynamicBranch.Options.Count} isDynamic={dynamicBranch.IsDynamic} key={dynamicBranch.CompileKey ?? "null"}");
        Console.WriteLine($"[dynamic] x={OrderOf(dynamicGraph, x)} y={OrderOf(dynamicGraph, y)}");

        router.Mode = RouterCompileMode.Static;
        router.Selection = RouteKey.A;
        var staticGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
        var staticBranch = (BranchSegment)staticGraph.Entries[1];
        Console.WriteLine($"[static] options={staticBranch.Options.Count} isDynamic={staticBranch.IsDynamic} key={staticBranch.CompileKey}");
        Console.WriteLine($"[static] x={OrderOf(staticGraph, x)} y={OrderOf(staticGraph, y)}");

        router.Mode = RouterCompileMode.Dynamic;
        var cone = (await compiler.CompileAsync(y, CompileRole.Terminal))[0];
        Console.WriteLine($"[terminal] entries={string.Join(",", cone.Entries.Select(e => e.GetType().Name))}");
        Console.WriteLine($"[terminal] x={OrderOf(cone, x)} y={OrderOf(cone, y)}; containsSource={cone.TryGetCompileInfo(source, out _)}");

        router.Selection = RouteKey.B;   // the cone kept only the branch that reaches y
        var session = new RuntimeContext { Data = "seed", Target = y };
        await new RuntimeEngine().RunAsync(cone, session, CancellationToken.None);
        Console.WriteLine($"[terminal] status={session.Status} targetReached={session.TargetReached} depth={CompiledOutline.Of(cone).Count}");
    }
}
```

## 10. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
