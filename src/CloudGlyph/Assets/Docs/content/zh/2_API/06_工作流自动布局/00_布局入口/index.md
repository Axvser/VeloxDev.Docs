# 布局入口

两个扩展重载构成完整的公开入口：一个针对树，一个针对节点的可达子图。选项塑造快照、求解与应用。

命名空间：`VeloxDev.WorkflowSystem`。

## WorkflowLayoutEx

**签名：** `static class WorkflowLayoutEx`

### Arrange（树）

**签名：** `static WorkflowLayoutResult Arrange(this ITreeComponent tree, WorkflowLayoutOptions? options = null)`

经树助手的求解器排列整棵树；助手未实现 `IWorkflowLayoutHost` 时改用新的 `DefaultWorkflowLayoutSolver`。

**返回：** `WorkflowLayoutResult`。**异常：** null 树抛 `ArgumentNullException`。

### Arrange（节点）

**签名：** `static WorkflowLayoutResult Arrange(this INodeComponent node, WorkflowLayoutOptions? options = null)`

经 `node.Parent` 找到树，设置 `options.StartNode = node` 并排列从它可达的子图。只有可达节点可移动；其他有限节点保持为固定障碍。

**返回：** `WorkflowLayoutResult`。**异常：** null 节点抛 `ArgumentNullException`；节点未挂载到树时抛 `ArgumentException`。

两个重载走同一助手。`WorkflowLayoutOptions.DryRun` 由应用器处理，因此试运行返回 `Applied == false` 的正常结果。

## WorkflowLayoutTraversal

**签名：** `enum WorkflowLayoutTraversal`

| 值 | 含义 |
| --- | --- |
| `Downstream` | 只沿发送端到接收端的连线。 |
| `Upstream` | 只沿接收端到发送端的连线。 |
| `Both` | 双向跟随连线。 |

## WorkflowLayoutOptions

**签名：** `sealed class WorkflowLayoutOptions`

| 成员 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `TileSize` | `double` | `256` | 分离网格一个瓦片的边长；只影响性能。 |
| `ColumnGap` | `double` | `64` | 相邻节点最小水平间距。 |
| `RowGap` | `double` | `32` | 相邻节点最小垂直间距。 |
| `MaxSweeps` | `int` | `8` | 分离阶段扫描预算；小于一按一处理。 |
| `ParallelThreshold` | `int` | `64` | 达到该数量的带可并行执行。 |
| `PositionTolerance` | `double` | `8` | 保留既有放置的每轴距离；`0` 为严格规范布局。 |
| `StartNode` | `INodeComponent?` | `null` | 作用域节点；null 表示整棵树。 |
| `Traversal` | `WorkflowLayoutTraversal` | `Downstream` | 从 `StartNode` 跟随的方向。 |
| `MaxDepth` | `int` | `0` | 从起点起的跳数上限；`0` 不限。 |
| `PinStartNode` | `bool` | `true` | 起点是否固定。 |
| `Pinned` | `Func<INodeComponent, bool>?` | `null` | 每节点求值一次的谓词；钉住节点永不移动但仍约束邻居。 |
| `DryRun` | `bool` | `false` | 求解但不写回；结果报告 `Applied == false`。 |
| `MeasureCost` | `bool` | `true` | 默认成本是否统计重叠与交叉。 |

起点必须属于树且具有有限世界几何，否则问题构建器抛 `ArgumentException`。无论 `PositionTolerance` 如何，硬重叠与最小间距总会被修复。

## WorkflowLayoutResult

**签名：** `sealed class WorkflowLayoutResult`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowLayoutResult(WorkflowLayoutSolution solution, bool applied, int appliedCount, bool dryRun, int skippedCount = 0)` | 构造函数 | null 解抛 `ArgumentNullException`。 |
| `Solution` | `WorkflowLayoutSolution` | 已应用或跳过的解。 |
| `Applied` | `bool` | 是否写入了任何锚点。 |
| `AppliedCount` | `int` | 写入节点数。 |
| `DryRun` | `bool` | 是否因 `DryRun` 跳过应用。 |
| `SkippedCount` | `int` | 因活动锚点、层或父节点不再匹配快照而跳过的移动节点数。 |

跳过保护求解与应用之间发生的并发编辑；应用器绝不覆盖已变化的锚点或已离开树的节点。

## 示例

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
