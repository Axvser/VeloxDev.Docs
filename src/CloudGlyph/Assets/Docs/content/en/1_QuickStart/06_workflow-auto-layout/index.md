# Workflow auto-layout

`Arrange` solves a layout for a tree or for the subgraph reachable from one node and writes the result back as one undoable action. The default solver aligns each hierarchy to its parent's centre and then separates overlapping tiles; the host chooses the scope, the traversal, how strictly existing positions are kept, and whether to apply at all.

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- A tree with nodes, sizes and links. No adapter or view is involved: layout works on the model.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. How the default solver reads a graph

The default planner runs two stages: `HierarchyAlignmentStage` places every node on its parent hierarchy's centre line, and `TileSeparationStage` repairs whatever still conflicts.

- A parent with several children becomes one **column to the right** of the parent, stacked with `RowGap` and centred on the parent's vertical centre.
- A fan-in merge is centred on its parents' bounding box.
- A single child is centred on its parent.

A node belongs to the tile that contains its centre; `TileSize` only changes performance, not the intended relationship.

**Expected result:** for a 100×40 parent at `(0,100)` and three 100×20 children, the canonical column is `x=164` and `y=80, 110, 140` with `ColumnGap=64`, `RowGap=10`.

## 4. Arrange a node's subgraph

```csharp
var result = parent.Arrange(new WorkflowLayoutOptions
{
    RowGap = 10,
    ColumnGap = 64,
    TileSize = 64,
    PositionTolerance = 0,
});
```

The node overload finds the tree through `Parent` and asks its helper for the registered `IWorkflowLayoutSolver`. If the helper does not implement `IWorkflowLayoutHost`, the default solver is used. `tree.Arrange(options)` does the same for the whole tree.

**Expected result:** `result.Applied == true`, `result.AppliedCount == 3`, and the three children move to the canonical column.

## 5. Scope, traversal and pinning

With a `StartNode` (set automatically by the node overload), only the reachable nodes move. Every other finite node stays in the problem as a fixed obstacle.

- `Traversal` chooses `Downstream`, `Upstream` or `Both`.
- `MaxDepth` limits the hops from the start node; `0` means unlimited.
- `PinStartNode` defaults to `true`, so the arrangement grows away from the node the user chose.
- `Pinned` is a predicate evaluated once per node during snapshot building; pinned nodes are never written, but still constrain their neighbours.
- A node with non-finite world geometry is skipped and reported as a diagnostic.

**Expected result:** arranging downstream from the parent leaves the parent's anchor unchanged while its children are placed.

## 6. Tolerance: strict, default and loose

`PositionTolerance` is the per-axis distance within which an existing placement is kept instead of being aligned to the canonical target.

- `0` — strict canonical layout; the result does not depend on where the user left the nodes.
- `8` — the default; a group already within 8 units of its canonical position keeps its placement.
- `32` — loose; only real conflicts are repaired.

Hard overlaps and minimum gaps are always repaired, regardless of the tolerance.

**Expected result:** at tolerance `0`, two trees with wildly different starting positions produce the same solved coordinates.

## 7. Dry run, cost and undo

`DryRun` stops short of writing: the pipeline solves and returns a normal result with `Applied == false` and `DryRun == true`.

```csharp
var dry = parent.Arrange(new WorkflowLayoutOptions { DryRun = true });
```

`result.Solution.Cost` reports `Overlaps`, `Crossings`, `Displacement`, `CostMeasured` and `CrossingsApproximate`. `MeasureCost = false` skips the graph-scaled overlap and crossing counts; displacement and content bounds are always reported.

Applying writes each changed node's **world** anchor through `StandardSetAnchor`, preserving its layer, and wraps all writes in one `IActionPair`:

```csharp
tree.GetHelper().Undo();   // one step restores every anchor
```

A node whose live anchor, layer or parent changed between solve and apply is skipped (`result.SkippedCount`), so a concurrent edit is never overwritten.

**Expected result:** a dry run writes nothing; one Undo after a real arrangement restores the original anchors.

## 8. Replace the solver

Register a custom solution on one tree's helper; it never affects another tree.

```csharp
if (tree.GetHelper() is IWorkflowLayoutHost host)
    host.LayoutSolver = new DefaultWorkflowLayoutSolver(
        planner: new DefaultWorkflowLayoutPlanner(new TolerancePositionPolicy()),
        cost: new DefaultWorkflowLayoutCost());
```

Implement `IWorkflowLayoutSolver` to replace the whole composition, or pass a different `IWorkflowLayoutPlanner` / `IWorkflowLayoutCost` to the default one.

## 9. Verification

```powershell
dotnet run
```

Expected output:

```text
[layout] applied=True count=3 dryRun=False skipped=0
[layout] c1 -> Anchor(164,80,0)
[layout] c2 -> Anchor(164,110,0)
[layout] c3 -> Anchor(164,140,0)
[layout] overlaps=0 crossings=0 displacement=1873.09 measured=True
[layout] after undo: c1=Anchor(500,-300,0)
[layout] dry applied=False dryRun=True c1=Anchor(500,-300,0)
[layout] scoped parentMoved=False
```

## 10. Complete code

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.AutoLayout;

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
public partial class DemoNode
{
    public DemoNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Node";
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

    public static void Main()
    {
        var tree = new DemoTree();
        var parent = new DemoNode("parent") { Anchor = new Anchor(0, 100, 0), Size = new Size(100, 40) };
        var children = new[]
        {
            new DemoNode("c1") { Anchor = new Anchor(500, -300, 0), Size = new Size(100, 20) },
            new DemoNode("c2") { Anchor = new Anchor(1000, 900, 0), Size = new Size(100, 20) },
            new DemoNode("c3") { Anchor = new Anchor(0, 0, 0), Size = new Size(100, 20) },
        };
        foreach (var n in new INodeComponent[] { parent, children[0], children[1], children[2] })
            tree.GetHelper().CreateNode(n);

        parent.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
        foreach (var child in children)
        {
            child.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
            Wire(tree, parent.Output, child.Input);
        }

        var options = new WorkflowLayoutOptions
        {
            RowGap = 10,
            ColumnGap = 64,
            TileSize = 64,
            PositionTolerance = 0,
        };
        var result = parent.Arrange(options);
        Console.WriteLine($"[layout] applied={result.Applied} count={result.AppliedCount} dryRun={result.DryRun} skipped={result.SkippedCount}");
        foreach (var child in children)
            Console.WriteLine($"[layout] {child.Title} -> {child.Anchor}");

        Console.WriteLine($"[layout] overlaps={result.Solution.Cost.Overlaps} crossings={result.Solution.Cost.Crossings} displacement={result.Solution.Cost.Displacement:0.##} measured={result.Solution.Cost.CostMeasured}");

        // One undo restores every anchor the arrangement wrote.
        tree.GetHelper().Undo();
        Console.WriteLine($"[layout] after undo: c1={children[0].Anchor}");

        // A dry run solves but writes nothing.
        var dry = parent.Arrange(new WorkflowLayoutOptions { DryRun = true });
        Console.WriteLine($"[layout] dry applied={dry.Applied} dryRun={dry.DryRun} c1={children[0].Anchor}");

        // Scope: only the reachable downstream subgraph moves; the start node stays put.
        var beforeParent = parent.Anchor;
        parent.Arrange(new WorkflowLayoutOptions { Traversal = WorkflowLayoutTraversal.Downstream, PinStartNode = true });
        Console.WriteLine($"[layout] scoped parentMoved={!Equals(beforeParent, parent.Anchor)}");
    }
}
```

## 11. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
