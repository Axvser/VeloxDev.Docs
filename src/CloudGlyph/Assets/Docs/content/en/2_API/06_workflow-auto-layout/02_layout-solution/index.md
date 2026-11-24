# Layout solution

A solution is the solved positions plus the cost of getting there. It owns the snapshot but nothing live, so it can be inspected or discarded without touching the tree; only the applier writes it back.

Namespace: `VeloxDev.WorkflowSystem`.

## WorkflowLayoutPlacement

**Signature:** `readonly struct WorkflowLayoutPlacement`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutPlacement(int index, double originalX, double originalY, double x, double y, double width, double height, bool isPinned)` | constructor | Snapshot and solved position. |
| `Index` | `int` | Node index in the problem. |
| `OriginalX` / `OriginalY` | `double` | Snapshot world edges. |
| `X` / `Y` | `double` | Solved world edges. |
| `Width` / `Height` | `double` | World extent. |
| `IsPinned` | `bool` | Pin state. |
| `DeltaX` / `DeltaY` | `double` | Requested displacement. |
| `Moved` | `bool` | True when the solved X or Y differs from the snapshot. |

## WorkflowLayoutCostBreakdown

**Signature:** `readonly struct WorkflowLayoutCostBreakdown`

| Member | Type | Description |
| --- | --- | --- |
| `CostMeasured` | `bool` | Whether overlaps and crossings were measured. |
| `Crossings` | `int` | Crossing pairs, measured on solved centre lines. |
| `CrossingsApproximate` | `bool` | Whether crossings are an estimate rather than a published-curve count. |
| `Overlaps` | `int` | Node pairs overlapping with positive area. |
| `OverlapArea` | `double` | Total overlapping area. |
| `Displacement` | `double` | Sum of Euclidean displacement of every moved node. |
| `MaxDisplacement` | `double` | Largest single displacement. |
| `Bounds` | `WorkflowBounds` | Union of the solved rectangles. |

Displacement and bounds are always linear and always reported. Overlap and crossing counts scale with the graph and can be disabled with `MeasureCost = false`; the breakdown then sets `CostMeasured = false`.

## WorkflowLayoutSolution

**Signature:** `sealed class WorkflowLayoutSolution`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutSolution(WorkflowLayoutProblem problem, WorkflowLayoutOptions options, IReadOnlyList<WorkflowLayoutPlacement> placements, WorkflowLayoutCostBreakdown cost, IReadOnlyList<string> diagnostics)` | constructor | Throws `ArgumentNullException` for any null reference. |
| `Problem` | `WorkflowLayoutProblem` | The snapshot solved. |
| `Options` | `WorkflowLayoutOptions` | Options used for the solve. |
| `Placements` | `IReadOnlyList<WorkflowLayoutPlacement>` | One per problem node, in problem order. |
| `Cost` | `WorkflowLayoutCostBreakdown` | Measured cost. |
| `Diagnostics` | `IReadOnlyList<string>` | Notes produced during the solve. |
| `IsEmpty` | `bool` | No placements. |
| `HasMoves` | `bool` | At least one placement moves its node. |

## WorkflowLayoutAxis

**Signature:** `enum WorkflowLayoutAxis` — `Vertical` or `Horizontal`.

## WorkflowLayoutPositionDecision

**Signature:** `readonly struct WorkflowLayoutPositionDecision`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowLayoutPositionDecision(int nodeIndex, double currentX, double currentY, double targetX, double targetY, bool isPinned, bool hasHardViolation, double tolerance, WorkflowLayoutAxis axis)` | constructor | One question for the policy. |
| `NodeIndex` | `int` | Node considered. |
| `CurrentX` / `CurrentY` | `double` | Current edges. |
| `TargetX` / `TargetY` | `double` | Proposed edges. |
| `IsPinned` | `bool` | Pin state. |
| `HasHardViolation` | `bool` | Whether the node currently overlaps or under-spaces a neighbour. |
| `Tolerance` | `double` | Configured tolerance for this decision. |
| `Axis` | `WorkflowLayoutAxis` | Axis the proposal moves along. |
| `AxisDistance` | `double` | Absolute distance asked for along `Axis`. |

`HasHardViolation` describes the **current** rectangles, not the proposal, so a policy can tell "already broken" from "merely not canonical".

## IWorkflowLayoutPositionPolicy

**Signature:** `interface IWorkflowLayoutPositionPolicy`

| Member | Type | Description |
| --- | --- | --- |
| `ShouldApply(WorkflowLayoutPositionDecision decision)` | `bool` | Whether the proposed position may be applied. |

The policy governs soft alignment only: a stage always fixes hard violations regardless of the answer.

## TolerancePositionPolicy

**Signature:** `sealed class TolerancePositionPolicy : IWorkflowLayoutPositionPolicy`

**Signature:** `bool ShouldApply(WorkflowLayoutPositionDecision decision)`

Returns `false` for a pinned node; `true` for a hard violation; `false` when the tolerance is zero or below; otherwise `AxisDistance > Tolerance`. A zero tolerance therefore makes the separation stage repair hard violations only, leaving canonical placement to the alignment stage.

## Example

```csharp
var result = tree.Arrange(new WorkflowLayoutOptions { PositionTolerance = 0 });
var solution = result.Solution;

Console.WriteLine($"{solution.Placements.Count} moved={solution.HasMoves}");
Console.WriteLine($"{solution.Cost.Overlaps} {solution.Cost.Crossings} {solution.Cost.Displacement:0.##}");
Console.WriteLine(string.Join(" | ", solution.Diagnostics));

var policy = new TolerancePositionPolicy();
var decision = new WorkflowLayoutPositionDecision(
    0, 0, 0, 100, 0, isPinned: false, hasHardViolation: false, tolerance: 8,
    WorkflowLayoutAxis.Horizontal);
Console.WriteLine(policy.ShouldApply(decision));   // True
```
