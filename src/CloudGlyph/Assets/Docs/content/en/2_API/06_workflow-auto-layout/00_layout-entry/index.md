# Layout entry

Two extension overloads are the whole public entry: one for a tree, one for a node's reachable subgraph. Options shape the snapshot, the solve and the apply.

Namespace: `VeloxDev.WorkflowSystem`.

## WorkflowLayoutEx

**Signature:** `static class WorkflowLayoutEx`

### Arrange (tree)

**Signature:** `static WorkflowLayoutResult Arrange(this ITreeComponent tree, WorkflowLayoutOptions? options = null)`

Arranges the whole tree through its helper's solver, or through a new `DefaultWorkflowLayoutSolver` when the helper does not implement `IWorkflowLayoutHost`.

**Returns:** `WorkflowLayoutResult`. **Exceptions:** `ArgumentNullException` for a null tree.

### Arrange (node)

**Signature:** `static WorkflowLayoutResult Arrange(this INodeComponent node, WorkflowLayoutOptions? options = null)`

Finds the tree through `node.Parent`, sets `options.StartNode = node` and arranges the subgraph reachable from it. Only reachable nodes are movable; every other finite node stays as a fixed obstacle.

**Returns:** `WorkflowLayoutResult`. **Exceptions:** `ArgumentNullException` for a null node; `ArgumentException` when the node is not attached to a tree.

Both overloads go through the same helper. `WorkflowLayoutOptions.DryRun` is honoured by the applier, so a dry run returns a normal result with `Applied == false`.

## WorkflowLayoutTraversal

**Signature:** `enum WorkflowLayoutTraversal`

| Value | Meaning |
| --- | --- |
| `Downstream` | Follow sender-to-receiver links only. |
| `Upstream` | Follow receiver-to-sender links only. |
| `Both` | Follow links in both directions. |

## WorkflowLayoutOptions

**Signature:** `sealed class WorkflowLayoutOptions`

| Member | Type | Default | Description |
| --- | --- | --- | --- |
| `TileSize` | `double` | `256` | Edge length of one separation-grid tile; performance only. |
| `ColumnGap` | `double` | `64` | Minimum horizontal gap between adjacent nodes. |
| `RowGap` | `double` | `32` | Minimum vertical gap between adjacent nodes. |
| `MaxSweeps` | `int` | `8` | Sweep budget for a separation stage; below one is treated as one. |
| `ParallelThreshold` | `int` | `64` | Band count at or above which bands may run in parallel. |
| `PositionTolerance` | `double` | `8` | Per-axis distance within which an existing placement is kept. `0` is strict canonical layout. |
| `StartNode` | `INodeComponent?` | `null` | Scope node; null means the whole tree. |
| `Traversal` | `WorkflowLayoutTraversal` | `Downstream` | Direction followed from `StartNode`. |
| `MaxDepth` | `int` | `0` | Hop limit from the start node; `0` is unlimited. |
| `PinStartNode` | `bool` | `true` | Whether the start node stays fixed. |
| `Pinned` | `Func<INodeComponent, bool>?` | `null` | Predicate evaluated once per node; pinned nodes never move but still constrain neighbours. |
| `DryRun` | `bool` | `false` | Solve but do not write; the result reports `Applied == false`. |
| `MeasureCost` | `bool` | `true` | Whether the default cost counts overlaps and crossings. |

A start node must belong to the tree and have finite world geometry, or the problem builder throws `ArgumentException`. Hard overlaps and minimum gaps are always repaired, whatever `PositionTolerance` says.

## WorkflowLayoutResult

**Signature:** `sealed class WorkflowLayoutResult`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutResult(WorkflowLayoutSolution solution, bool applied, int appliedCount, bool dryRun, int skippedCount = 0)` | constructor | Throws `ArgumentNullException` for a null solution. |
| `Solution` | `WorkflowLayoutSolution` | The solved solution, applied or skipped. |
| `Applied` | `bool` | Whether any anchor was written. |
| `AppliedCount` | `int` | Number of nodes written. |
| `DryRun` | `bool` | Whether the apply was skipped because of `DryRun`. |
| `SkippedCount` | `int` | Moved nodes skipped because their live anchor, layer or parent no longer matched the snapshot. |

A skip protects a concurrent edit made between solve and apply; the applier never overwrites an anchor that has already changed or a node that has left the tree.

## Example

```csharp
var options = new WorkflowLayoutOptions
{
    RowGap = 10,
    ColumnGap = 64,
    TileSize = 64,
    PositionTolerance = 0,
};

var result = parent.Arrange(options);
Console.WriteLine($"{result.Applied} {result.AppliedCount} {result.DryRun} {result.SkippedCount}");

var dry = parent.Arrange(new WorkflowLayoutOptions { DryRun = true });
Console.WriteLine(dry.Applied);    // False
```
