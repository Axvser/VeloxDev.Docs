# 管线与求解器

求解器组合快照、流水线与应用器。每个扩展缝都可独立替换，注册在一棵树助手上的自定义解绝不会泄漏到另一棵树。

命名空间：`VeloxDev.WorkflowSystem`。

## IWorkflowLayoutSolver

**签名：** `interface IWorkflowLayoutSolver`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Arrange(ITreeComponent tree, WorkflowLayoutOptions options)` | `WorkflowLayoutResult` | 为一棵树求解并应用。 |

## IWorkflowLayoutHost

**签名：** `interface IWorkflowLayoutHost`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `LayoutSolver` | `IWorkflowLayoutSolver` | 本树使用的解。 |
| `Arrange(INodeComponent? start, WorkflowLayoutOptions? options = null)` | `WorkflowLayoutResult` | 排列树，可选限定到 `start`。 |

`TreeHelper<T>` 实现该接口；其 `LayoutSolver` 默认为 `DefaultWorkflowLayoutSolver`。

## IWorkflowLayoutPlanner

**签名：** `interface IWorkflowLayoutPlanner`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `CreateStages(WorkflowLayoutProblem problem, WorkflowLayoutOptions options)` | `IReadOnlyList<IWorkflowLayoutStage>` | 本次求解的有序阶段。 |

## IWorkflowLayoutStage

**签名：** `interface IWorkflowLayoutStage`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Name` | `string` | 用于诊断的稳定名称。 |
| `Execute(WorkflowLayoutState state, WorkflowLayoutContext context)` | `void` | 读问题，只写自己拥有的数组。 |

## IWorkflowLayoutCost

**签名：** `interface IWorkflowLayoutCost`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Measure(WorkflowLayoutProblem problem, WorkflowLayoutState state, WorkflowLayoutContext context)` | `WorkflowLayoutCostBreakdown` | 快照与求解数组的纯函数。 |

## IWorkflowLayoutApplier

**签名：** `interface IWorkflowLayoutApplier`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Apply(WorkflowLayoutProblem problem, WorkflowLayoutSolution solution)` | `WorkflowLayoutResult` | 以一步可撤销操作写回解。 |

## WorkflowLayoutPipeline

**签名：** `sealed class WorkflowLayoutPipeline`

**构造函数：** `WorkflowLayoutPipeline(IWorkflowLayoutPlanner? planner = null, IWorkflowLayoutCost? cost = null)` —— 默认 `DefaultWorkflowLayoutPlanner` 与 `DefaultWorkflowLayoutCost`。

### Solve

**签名：** `WorkflowLayoutSolution Solve(WorkflowLayoutProblem problem, WorkflowLayoutOptions? options = null, WorkflowLayoutContext? context = null)`

按序运行规划器阶段，重新断言钉住位置，测量成本并构建放置。它从不解引用活动节点或连线；应用是独立一步。null 问题抛 `ArgumentNullException`。

## DefaultWorkflowLayoutSolver

**签名：** `sealed class DefaultWorkflowLayoutSolver : IWorkflowLayoutSolver`

**构造函数：** `DefaultWorkflowLayoutSolver(IWorkflowLayoutPlanner? planner = null, IWorkflowLayoutCost? cost = null)`

`Arrange` 用 `WorkflowLayoutProblemBuilder.Build` 构建问题，经 `WorkflowLayoutPipeline` 求解，再用 `WorkflowLayoutApplier` 应用。null 树抛 `ArgumentNullException`。

## DefaultWorkflowLayoutPlanner

**签名：** `sealed class DefaultWorkflowLayoutPlanner : IWorkflowLayoutPlanner`

**构造函数：** `DefaultWorkflowLayoutPlanner(IWorkflowLayoutPositionPolicy? policy = null)` —— 默认 `TolerancePositionPolicy`。

`CreateStages` 返回 `[HierarchyAlignmentStage, TileSeparationStage(policy)]`。此管线版本没有分层、排序或布线阶段。

## HierarchyAlignmentStage

**签名：** `sealed class HierarchyAlignmentStage : IWorkflowLayoutStage` —— `Name` 为 `"hierarchy-alignment"`。

- 有两个或更多子节点的父节点把它们堆在右侧一列，以 `RowGap` 分隔并以其垂直中心居中。
- 只有一个父节点的节点居中到该父节点，并放在其右侧一个 `ColumnGap` 处。
- 有两个或更多父节点的节点居中到它们的包围盒，并放在最右父节点右侧。
- 按拓扑序运行；剩余环上节点按索引补入。扇出优先于单父与扇入规则；含钉住子节点的扇出组整组跳过。
- `PositionTolerance` 为零时写规范位置；正值保留每轴该距离内的既有放置。钉住节点永不写入。

## TileSeparationStage

**签名：** `sealed class TileSeparationStage : IWorkflowLayoutStage` —— `Name` 为 `"tile-separation"`。

**构造函数：** `TileSeparationStage(IWorkflowLayoutPositionPolicy? policy = null)`。

每个节点属于包含其中心的瓦片。**列带**共享瓦片列，**行带**共享瓦片行；带写入互不相交的节点，是并行工作的单位。每次扫描在每个列带自上而下推开节点，再在每个行带自左向右推开；阶段从当前位置出发，不发明对齐目标。最后一遍单线程修复两个带方向都看不到的正面积重叠。硬违规无论策略如何都会移动；钉住节点永不写入。

## DefaultWorkflowLayoutCost

**签名：** `sealed class DefaultWorkflowLayoutCost : IWorkflowLayoutCost`

测量位移、内容范围、重叠与交叉。交叉使用求解后节点中心之间的直线段，因此移动过的节点会改变计数；`CrossingsApproximate` 记录该计数描述中心线而非绘制曲线。重叠与交叉对经临时瓦片索引查找。null 参数抛 `ArgumentNullException`。

## WorkflowLayoutApplier

**签名：** `sealed class WorkflowLayoutApplier : IWorkflowLayoutApplier`

**构造函数：** `WorkflowLayoutApplier(ITreeComponent tree)` —— null 抛 `ArgumentNullException`。

`Apply` 跳过钉住与未移动节点，并拒绝为另一问题产生的解（`ArgumentException`）。活动世界锚点、层或父节点已不匹配快照的移动节点被跳过并计数。所有写入经 `StandardSetAnchor` 并保留层，包在一个 `ActionPair` 中；提交后树只标脏一次。

## 示例

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
