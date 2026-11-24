# Layout snapshot

The snapshot is an immutable copy of the node rectangles and links, built on the calling thread. Stages may run on worker threads and never touch the live model.

Namespace: `VeloxDev.WorkflowSystem`.

## WorkflowLayoutNode

**Signature:** `readonly struct WorkflowLayoutNode`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutNode(int index, double x, double y, double width, double height, int layer, bool isPinned)` | constructor | One world-space node rectangle. |
| `Index` | `int` | Position in the problem's node list. |
| `X` / `Y` | `double` | World-space left / top edge. |
| `Width` / `Height` | `double` | World-space extent. |
| `Layer` | `int` | Node layer, preserved on apply. |
| `IsPinned` | `bool` | Whether the node must never move. |
| `Right` / `Bottom` | `double` | Far edges. |
| `CentreX` / `CentreY` | `double` | Rectangle centres. |

## WorkflowLayoutEdge

**Signature:** `readonly struct WorkflowLayoutEdge`

Members: constructor `(int sender, int receiver)`; read-only `Sender`, `Receiver` node indices. The snapshot keeps no link reference.

## WorkflowLayoutProblem

**Signature:** `sealed class WorkflowLayoutProblem`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutProblem(IReadOnlyList<WorkflowLayoutNode> nodes, IReadOnlyList<WorkflowLayoutEdge> edges, IReadOnlyList<INodeComponent> sources, IReadOnlyList<int>? skippedIndices = null)` | constructor | Copies the data; throws `ArgumentNullException` for null and `ArgumentException` when `sources` and `nodes` differ in length. |
| `Nodes` | `IReadOnlyList<WorkflowLayoutNode>` | Node rectangles. |
| `Edges` | `IReadOnlyList<WorkflowLayoutEdge>` | Directed links between them. |
| `Sources` | `IReadOnlyList<INodeComponent>` | Live nodes, aligned position for position with `Nodes`; for the applier only. |
| `SkippedIndices` | `IReadOnlyList<int>` | Original indices omitted for non-finite geometry. |
| `HasSkippedNodes` | `bool` | Whether any node was omitted. |
| `ContentBounds` | `WorkflowBounds` | Union of the node rectangles. |
| `IsEmpty` | `bool` | No nodes. |

## WorkflowLayoutProblemBuilder

**Signature:** `static class WorkflowLayoutProblemBuilder`

### Build

**Signature:** `static WorkflowLayoutProblem Build(ITreeComponent tree, WorkflowLayoutOptions? options = null)`

Runs on the calling thread and is the only layout component that reads the model during snapshot building. It converts collapsed node geometry back to world coordinates with `GetWorldAnchor()`/`GetWorldSize()`, drops self-links and links with an endpoint outside the tree, and evaluates `options.Pinned` once per node. Nodes with `NaN`/infinite geometry are omitted with their edges and their original indices are recorded.

When `options.StartNode` is set, `Traverse` selects the reachable set and every node outside it is marked pinned; the start node is pinned when `PinStartNode` is true.

**Returns:** the immutable problem. **Exceptions:** `ArgumentNullException` for a null tree; `ArgumentException` when the start node does not belong to the tree or has non-finite geometry.

## WorkflowLayoutState

**Signature:** `sealed class WorkflowLayoutState`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutState(WorkflowLayoutProblem problem, WorkflowLayoutOptions options)` | constructor | Starts positions at the snapshot rectangles. |
| `Problem` / `Options` | | Read-only inputs. |
| `X` / `Y` | `double[]` | Current world-space left / top edges. |
| `Rank` | `int[]` | Reserved for a layering stage; initialised to `-1`. |
| `Order` | `int[]` | Reserved for an ordering stage; initialised to `-1`. |
| `RouteX` / `RouteY` | `double[]` | Reserved for a routing stage; one per edge, `NaN`. |
| `IsPinned(int index)` | `bool` | Snapshot pin state. |
| `HasMoved(int index)` | `bool` | Whether the node moved from its snapshot position. |
| `ResetToOriginal()` | `void` | Restores every position. |

The four arrays are indexed exactly like `Problem.Nodes`. A stage that writes positions must not write pinned entries; the pipeline re-asserts pinned positions after the last stage regardless. Arrays reserved for phases the current planner does not run stay at their initial values.

## WorkflowLayoutContext

**Signature:** `sealed class WorkflowLayoutContext`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutContext(CancellationToken cancellationToken = default, bool enableParallelism = true, int seed = 0, Action<string, double>? metricSink = null, Action<string>? diagnosticSink = null)` | constructor | Execution environment. |
| `CancellationToken` | `CancellationToken` | Cancels between bands and between stages. |
| `EnableParallelism` | `bool` | Whether stages may fan bands out. |
| `Seed` | `int` | Seed for randomised tie-breaking. |
| `MetricSink` | `Action<string, double>?` | Named measurements. |
| `DiagnosticSink` | `Action<string>?` | Human-readable notes. |
| `Report(string name, double value)` | `void` | Forwards a measurement to `MetricSink`. |
| `ReportDiagnostic(string message)` | `void` | Records a note and forwards it to `DiagnosticSink`. |

Diagnostics are collected per `Solve` and returned in `WorkflowLayoutSolution.Diagnostics`; a reused context does not carry the previous solve's notes.

## WorkflowBounds

**Signature:** `readonly struct WorkflowBounds` — also used by the geometry and minimap surfaces.

Members: init-only `Left`, `Top`, `Width`, `Height`; `Right`, `Bottom`, `IsEmpty`; static `FromNode`, `FromNodes`, `Union`. See [Geometry models](../../00_workflow-graph-model/03_geometry/index.md).

## Example

```csharp
var options = new WorkflowLayoutOptions { RowGap = 10, ColumnGap = 64 };
var problem = WorkflowLayoutProblemBuilder.Build(tree, options);
Console.WriteLine($"{problem.Nodes.Count} edges={problem.Edges.Count} skipped={problem.SkippedIndices.Count}");

var state = new WorkflowLayoutState(problem, options);
state.ResetToOriginal();
```
