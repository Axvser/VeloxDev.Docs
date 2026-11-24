# 布局解

解是求解后的位置加上到达它的成本。它拥有快照但不拥有任何活动对象，因此可以检查或丢弃而不触碰树；只有应用器会写回。

命名空间：`VeloxDev.WorkflowSystem`。

## WorkflowLayoutPlacement

**签名：** `readonly struct WorkflowLayoutPlacement`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutPlacement(int index, double originalX, double originalY, double x, double y, double width, double height, bool isPinned)` | 构造函数 | 快照与求解位置。 |
| `Index` | `int` | 问题中的节点索引。 |
| `OriginalX` / `OriginalY` | `double` | 快照世界边缘。 |
| `X` / `Y` | `double` | 求解世界边缘。 |
| `Width` / `Height` | `double` | 世界尺寸。 |
| `IsPinned` | `bool` | 钉住状态。 |
| `DeltaX` / `DeltaY` | `double` | 请求的位移。 |
| `Moved` | `bool` | 求解后的 X 或 Y 与快照不同时为真。 |

## WorkflowLayoutCostBreakdown

**签名：** `readonly struct WorkflowLayoutCostBreakdown`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `CostMeasured` | `bool` | 是否测量了重叠与交叉。 |
| `Crossings` | `int` | 交叉对数量，基于求解后中心线。 |
| `CrossingsApproximate` | `bool` | 交叉是否为估算而非发布曲线计数。 |
| `Overlaps` | `int` | 正面积重叠的节点对。 |
| `OverlapArea` | `double` | 总重叠面积。 |
| `Displacement` | `double` | 每个移动节点欧氏位移之和。 |
| `MaxDisplacement` | `double` | 最大单节点位移。 |
| `Bounds` | `WorkflowBounds` | 求解后矩形的并集。 |

位移与范围始终线性且始终报告。重叠与交叉计数随图规模增长，可用 `MeasureCost = false` 关闭；此时 `CostMeasured = false`。

## WorkflowLayoutSolution

**签名：** `sealed class WorkflowLayoutSolution`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutSolution(WorkflowLayoutProblem problem, WorkflowLayoutOptions options, IReadOnlyList<WorkflowLayoutPlacement> placements, WorkflowLayoutCostBreakdown cost, IReadOnlyList<string> diagnostics)` | 构造函数 | 任一 null 引用抛 `ArgumentNullException`。 |
| `Problem` | `WorkflowLayoutProblem` | 被求解的快照。 |
| `Options` | `WorkflowLayoutOptions` | 求解所用选项。 |
| `Placements` | `IReadOnlyList<WorkflowLayoutPlacement>` | 每个问题节点一个，按问题顺序。 |
| `Cost` | `WorkflowLayoutCostBreakdown` | 测量成本。 |
| `Diagnostics` | `IReadOnlyList<string>` | 求解期间产生的备注。 |
| `IsEmpty` | `bool` | 无放置。 |
| `HasMoves` | `bool` | 至少一个放置会移动节点。 |

## WorkflowLayoutAxis

**签名：** `enum WorkflowLayoutAxis` —— `Vertical` 或 `Horizontal`。

## WorkflowLayoutPositionDecision

**签名：** `readonly struct WorkflowLayoutPositionDecision`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutPositionDecision(int nodeIndex, double currentX, double currentY, double targetX, double targetY, bool isPinned, bool hasHardViolation, double tolerance, WorkflowLayoutAxis axis)` | 构造函数 | 向策略提出的一个问题。 |
| `NodeIndex` | `int` | 被考虑的节点。 |
| `CurrentX` / `CurrentY` | `double` | 当前边缘。 |
| `TargetX` / `TargetY` | `double` | 拟议边缘。 |
| `IsPinned` | `bool` | 钉住状态。 |
| `HasHardViolation` | `bool` | 节点当前是否与邻居重叠或间距不足。 |
| `Tolerance` | `double` | 本次决策的配置容差。 |
| `Axis` | `WorkflowLayoutAxis` | 拟议移动所在的轴。 |
| `AxisDistance` | `double` | 沿 `Axis` 要求的绝对距离。 |

`HasHardViolation` 描述**当前**矩形，不是拟议位置，因此策略能区分「已经违规」与「只是不规范」。

## IWorkflowLayoutPositionPolicy

**签名：** `interface IWorkflowLayoutPositionPolicy`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ShouldApply(WorkflowLayoutPositionDecision decision)` | `bool` | 拟议位置是否可应用。 |

策略只管辖软对齐：无论它怎么回答，阶段总会修复硬违规。

## TolerancePositionPolicy

**签名：** `sealed class TolerancePositionPolicy : IWorkflowLayoutPositionPolicy`

**签名：** `bool ShouldApply(WorkflowLayoutPositionDecision decision)`

钉住节点返回 `false`；硬违规返回 `true`；容差为零或以下返回 `false`；否则返回 `AxisDistance > Tolerance`。因此零容差让分离阶段只修硬违规，把规范放置留给对齐阶段。

## 示例

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
