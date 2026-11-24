# Pipeline and solver

The solver composes a snapshot, a pipeline and an applier. Each seam can be replaced independently, and a custom solution registered on one tree's helper never leaks into another tree.

Namespace: `VeloxDev.WorkflowSystem`.

## IWorkflowLayoutSolver

**Signature:** `interface IWorkflowLayoutSolver`

| Member | Type | Description |
| --- | --- | --- |
| `Arrange(ITreeComponent tree, WorkflowLayoutOptions options)` | `WorkflowLayoutResult` | Solves and applies for one tree. |

## IWorkflowLayoutHost

**Signature:** `interface IWorkflowLayoutHost`

| Member | Type | Description |
| --- | --- | --- |
| `LayoutSolver` | `IWorkflowLayoutSolver` | The solution used by this tree. |
| `Arrange(INodeComponent? start, WorkflowLayoutOptions? options = null)` | `WorkflowLayoutResult` | Arranges the tree, optionally scoped to `start`. |

`TreeHelper<T>` implements this interface; its `LayoutSolver` defaults to `DefaultWorkflowLayoutSolver`.

## IWorkflowLayoutPlanner

**Signature:** `interface IWorkflowLayoutPlanner`

| Member | Type | Description |
| --- | --- | --- |
| `CreateStages(WorkflowLayoutProblem problem, WorkflowLayoutOptions options)` | `IReadOnlyList<IWorkflowLayoutStage>` | Ordered stages for this solve. |

## IWorkflowLayoutStage

**Signature:** `interface IWorkflowLayoutStage`

| Member | Type | Description |
| --- | --- | --- |
| `Name` | `string` | Stable name for diagnostics. |
| `Execute(WorkflowLayoutState state, WorkflowLayoutContext context)` | `void` | Reads the problem, writes only the arrays it owns. |

## IWorkflowLayoutCost

**Signature:** `interface IWorkflowLayoutCost`

| Member | Type | Description |
| --- | --- | --- |
| `Measure(WorkflowLayoutProblem problem, WorkflowLayoutState state, WorkflowLayoutContext context)` | `WorkflowLayoutCostBreakdown` | Pure function of the snapshot and solved arrays. |

## IWorkflowLayoutApplier

**Signature:** `interface IWorkflowLayoutApplier`

| Member | Type | Description |
| --- | --- | --- |
| `Apply(WorkflowLayoutProblem problem, WorkflowLayoutSolution solution)` | `WorkflowLayoutResult` | Writes a solution back as one undoable step. |

## WorkflowLayoutPipeline

**Signature:** `sealed class WorkflowLayoutPipeline`

**Constructor:** `WorkflowLayoutPipeline(IWorkflowLayoutPlanner? planner = null, IWorkflowLayoutCost? cost = null)` — defaults to `DefaultWorkflowLayoutPlanner` and `DefaultWorkflowLayoutCost`.

### Solve

**Signature:** `WorkflowLayoutSolution Solve(WorkflowLayoutProblem problem, WorkflowLayoutOptions? options = null, WorkflowLayoutContext? context = null)`

Runs the planner's stages in order, re-asserts pinned positions, measures the cost and builds the placements. It never dereferences a live node or link; applying is a separate step. Throws `ArgumentNullException` for a null problem.

## DefaultWorkflowLayoutSolver

**Signature:** `sealed class DefaultWorkflowLayoutSolver : IWorkflowLayoutSolver`

**Constructor:** `DefaultWorkflowLayoutSolver(IWorkflowLayoutPlanner? planner = null, IWorkflowLayoutCost? cost = null)`

`Arrange` builds the problem with `WorkflowLayoutProblemBuilder.Build`, solves it through a `WorkflowLayoutPipeline`, and applies it with a `WorkflowLayoutApplier`. Throws `ArgumentNullException` for a null tree.

## DefaultWorkflowLayoutPlanner

**Signature:** `sealed class DefaultWorkflowLayoutPlanner : IWorkflowLayoutPlanner`

**Constructor:** `DefaultWorkflowLayoutPlanner(IWorkflowLayoutPositionPolicy? policy = null)` — defaults to `TolerancePositionPolicy`.

`CreateStages` returns `[HierarchyAlignmentStage, TileSeparationStage(policy)]`. There is no layering, ordering or routing stage in this pipeline version.

## HierarchyAlignmentStage

**Signature:** `sealed class HierarchyAlignmentStage : IWorkflowLayoutStage` — `Name` is `"hierarchy-alignment"`.

- A parent with two or more children stacks them in one column to its right, centred on its vertical centre with `RowGap` between them.
- A node with exactly one parent is centred on that parent and placed one `ColumnGap` to its right.
- A node with two or more parents is centred on their bounding box and placed to the right of the rightmost parent.
- The pass runs in topological order; remaining cycle nodes are appended in index order. Fan-out wins over the single-parent and fan-in rules; a fan-out group containing a pinned child is skipped.
- `PositionTolerance` zero writes the canonical position; a positive value keeps an existing placement within that distance on each axis. Pinned nodes are never written.

## TileSeparationStage

**Signature:** `sealed class TileSeparationStage : IWorkflowLayoutStage` — `Name` is `"tile-separation"`.

**Constructor:** `TileSeparationStage(IWorkflowLayoutPositionPolicy? policy = null)`.

Each node belongs to the tile containing its centre. A **column band** shares a tile column and a **row band** shares a tile row; bands write disjoint nodes and are the unit of parallel work. Each sweep pushes nodes apart top-to-bottom in every column band, then left-to-right in every row band; the stage starts from current positions and invents no alignment target. A final single-threaded pass repairs positive-area overlaps invisible to both band directions. Hard violations move regardless of the policy; pinned nodes are never written.

## DefaultWorkflowLayoutCost

**Signature:** `sealed class DefaultWorkflowLayoutCost : IWorkflowLayoutCost`

Measures displacement, content bounds, overlaps and crossings. Crossings use the straight segment between solved node centres, so a node that moved changes the count; `CrossingsApproximate` records that the count describes centre lines, not drawn curves. Overlap and crossing pairs are found through a temporary tile index. Throws `ArgumentNullException` for null arguments.

## WorkflowLayoutApplier

**Signature:** `sealed class WorkflowLayoutApplier : IWorkflowLayoutApplier`

**Constructor:** `WorkflowLayoutApplier(ITreeComponent tree)` — throws `ArgumentNullException` for null.

`Apply` skips pinned and unmoved nodes and refuses a solution produced for a different problem (`ArgumentException`). A moved node whose live world anchor, layer or parent no longer matches the snapshot is skipped and counted. All writes go through `StandardSetAnchor`, preserving the layer, and are wrapped in one `ActionPair`; the tree is marked dirty once after the submit.

## Example

```csharp
if (tree.GetHelper() is IWorkflowLayoutHost host)
{
    host.LayoutSolver = new DefaultWorkflowLayoutSolver(
        planner: new DefaultWorkflowLayoutPlanner(new TolerancePositionPolicy()),
        cost: new DefaultWorkflowLayoutCost());
}

var result = tree.Arrange(new WorkflowLayoutOptions { DryRun = true });
Console.WriteLine($"{result.Applied} {result.DryRun} {result.Solution.Cost.CostMeasured}");
```
