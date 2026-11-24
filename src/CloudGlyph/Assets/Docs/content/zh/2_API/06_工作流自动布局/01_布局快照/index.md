# 布局快照

快照是节点矩形与连线的不可变副本，在调用线程上构建。阶段可以跑在工作线程上，且从不触碰活动模型。

命名空间：`VeloxDev.WorkflowSystem`。

## WorkflowLayoutNode

**签名：** `readonly struct WorkflowLayoutNode`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutNode(int index, double x, double y, double width, double height, int layer, bool isPinned)` | 构造函数 | 一个世界空间节点矩形。 |
| `Index` | `int` | 在问题节点列表中的位置。 |
| `X` / `Y` | `double` | 世界空间左 / 上边缘。 |
| `Width` / `Height` | `double` | 世界空间尺寸。 |
| `Layer` | `int` | 节点层，应用时保留。 |
| `IsPinned` | `bool` | 是否永不移动。 |
| `Right` / `Bottom` | `double` | 远端边缘。 |
| `CentreX` / `CentreY` | `double` | 矩形中心。 |

## WorkflowLayoutEdge

**签名：** `readonly struct WorkflowLayoutEdge`

成员：构造函数 `(int sender, int receiver)`；只读 `Sender`、`Receiver` 节点索引。快照不保存连线引用。

## WorkflowLayoutProblem

**签名：** `sealed class WorkflowLayoutProblem`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutProblem(IReadOnlyList<WorkflowLayoutNode> nodes, IReadOnlyList<WorkflowLayoutEdge> edges, IReadOnlyList<INodeComponent> sources, IReadOnlyList<int>? skippedIndices = null)` | 构造函数 | 复制数据；null 抛 `ArgumentNullException`，`sources` 与 `nodes` 长度不同抛 `ArgumentException`。 |
| `Nodes` | `IReadOnlyList<WorkflowLayoutNode>` | 节点矩形。 |
| `Edges` | `IReadOnlyList<WorkflowLayoutEdge>` | 它们之间的有向连线。 |
| `Sources` | `IReadOnlyList<INodeComponent>` | 活动节点，与 `Nodes` 逐位对齐；仅供应用器。 |
| `SkippedIndices` | `IReadOnlyList<int>` | 因非有限几何被省略的原始索引。 |
| `HasSkippedNodes` | `bool` | 是否省略了节点。 |
| `ContentBounds` | `WorkflowBounds` | 节点矩形的并集。 |
| `IsEmpty` | `bool` | 无节点。 |

## WorkflowLayoutProblemBuilder

**签名：** `static class WorkflowLayoutProblemBuilder`

### Build

**签名：** `static WorkflowLayoutProblem Build(ITreeComponent tree, WorkflowLayoutOptions? options = null)`

在调用线程上运行，是快照阶段唯一读取模型的布局组件。它用 `GetWorldAnchor()`/`GetWorldSize()` 把坍缩几何还原为世界坐标，丢弃自连线和端点不在树中的连线，并对每个节点求值一次 `options.Pinned`。世界几何为 `NaN`/无穷的节点连同其边被省略，原始索引被记录。

设置 `options.StartNode` 时，`Traverse` 选出可达集，集外节点全部标记为钉住；`PinStartNode` 为 true 时起点也钉住。

**返回：** 不可变问题。**异常：** null 树抛 `ArgumentNullException`；起点不属于树或几何非有限时抛 `ArgumentException`。

## WorkflowLayoutState

**签名：** `sealed class WorkflowLayoutState`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutState(WorkflowLayoutProblem problem, WorkflowLayoutOptions options)` | 构造函数 | 位置从快照矩形开始。 |
| `Problem` / `Options` | | 只读输入。 |
| `X` / `Y` | `double[]` | 当前世界空间左 / 上边缘。 |
| `Rank` | `int[]` | 预留给分层阶段；初始 `-1`。 |
| `Order` | `int[]` | 预留给排序阶段；初始 `-1`。 |
| `RouteX` / `RouteY` | `double[]` | 预留给布线阶段；每边一项，`NaN`。 |
| `IsPinned(int index)` | `bool` | 快照钉住状态。 |
| `HasMoved(int index)` | `bool` | 节点是否离开快照位置。 |
| `ResetToOriginal()` | `void` | 恢复全部位置。 |

四个数组的索引与 `Problem.Nodes` 完全一致。写位置的阶段不得写钉住项；流水线在最后阶段后无论如何会重新断言钉住位置。当前规划器不运行的阶段所预留的数组保持初始值。

## WorkflowLayoutContext

**签名：** `sealed class WorkflowLayoutContext`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutContext(CancellationToken cancellationToken = default, bool enableParallelism = true, int seed = 0, Action<string, double>? metricSink = null, Action<string>? diagnosticSink = null)` | 构造函数 | 执行环境。 |
| `CancellationToken` | `CancellationToken` | 在带之间与阶段之间取消。 |
| `EnableParallelism` | `bool` | 阶段是否可扇出带。 |
| `Seed` | `int` | 随机平局决胜种子。 |
| `MetricSink` | `Action<string, double>?` | 命名测量。 |
| `DiagnosticSink` | `Action<string>?` | 人类可读备注。 |
| `Report(string name, double value)` | `void` | 把测量转发给 `MetricSink`。 |
| `ReportDiagnostic(string message)` | `void` | 记录备注并转发给 `DiagnosticSink`。 |

诊断按 `Solve` 收集并放进 `WorkflowLayoutSolution.Diagnostics`；复用的上下文不会带入上一次求解的备注。

## WorkflowBounds

**签名：** `readonly struct WorkflowBounds` —— 几何与小地图表面也使用。

成员：init-only `Left`、`Top`、`Width`、`Height`；`Right`、`Bottom`、`IsEmpty`；静态 `FromNode`、`FromNodes`、`Union`。见[几何模型](../../00_工作流图模型/03_几何模型/index.md)。

## 示例

```csharp
var options = new WorkflowLayoutOptions { RowGap = 10, ColumnGap = 64 };
var problem = WorkflowLayoutProblemBuilder.Build(tree, options);
Console.WriteLine($"{problem.Nodes.Count} edges={problem.Edges.Count} skipped={problem.SkippedIndices.Count}");

var state = new WorkflowLayoutState(problem, options);
state.ResetToOriginal();
```
