# 工作流自动布局

布局是两阶段流水线：先用层级对齐阶段做拓扑排序并摆放扇出组，再用瓦片分离阶段反复扫描空间索引，直到重叠低于容差。对齐阶段接近线性；分离在最坏情况下是二次，因为落在同一瓦片里的节点会被两两比较。

记号：$n$ 个节点，$e$ 条边，最大度 $d$，扫描 $s$ 轮（最多 8），节点 $i$ 的邻域候选 $k_i$。

## 代价模型

| 操作 | 时间 | 出处 |
|---|---|---|
| 问题快照 | $O(n + e)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutProblemBuilder.cs:25` |
| 范围遍历（下游 / 上游 / 双向） | $O(n + e)$ BFS | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutProblemBuilder.cs:156` |
| 层级对齐 | $O((n + e)\log n + e d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/HierarchyAlignmentStage.cs:28` |
| 瓦片分离，单轮 | 每带 $O(n) + O(\sum m^2)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:35` |
| 全局重叠修复 | 最坏 $O(\text{轮数} \cdot n^2 \log n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:331` |
| 代价测量 | $O(n + e + \sum k_i)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/DefaultWorkflowLayoutCost.cs:19` |
| 应用 | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutApplier.cs:28` |

## 对齐排序，分离扫描

拓扑阶段用 `SortedSet<int>` 作为就绪队列，这正是 $\log n$ 因子的来源：

```csharp
var ready = new SortedSet<int>();
...
while (ready.Count > 0)
{
    var node = ready.Min;
    ...
    foreach (var next in outgoing[node])
        if (--indegree[next] == 0) ready.Add(next);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Layout/HierarchyAlignmentStage.cs:240-257`

分离每轮重建两次瓦片索引——纵向一次、横向一次——然后每个节点只与瓦片邻域返回的候选比较：

```csharp
for (var sweep = 0; sweep < maxSweeps; sweep++)
{
    ...
    var verticalIndex = BuildTileIndex(state, tileSize, originX, originY);
    var verticalBands = BuildBands(state, verticalIndex, vertical: true);
    ...
    if (MaxDelta(state, previousX, previousY) <= Epsilon) break;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:59-74`

在一个带内部，邻居检查是对已放置项的两两循环：

```csharp
foreach (var p in placed)
    if (!HorizontalOverlap(state, i, p)) continue;
    var required = state.Y[p] + problem.Nodes[p].Height + rowGap;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:120-123`

默认 `TileSize` 为 256 世界单位，分布良好的图给出小带、接近线性的扫描。稠密聚簇落在同一瓦片时退化为两两比较。整体上界为：

$$
T_{\text{arrange}}(n,e) = O((n+e)\log n + s\,n^2)
$$

其中 $s \le \texttt{MaxSweeps} = 8$。当最大位移低于 $\epsilon$ 时循环提前退出。

```plot
{
  "title": "布局：对齐与分离",
  "grid": true,
  "xAxis": { "domain": [0, 80] },
  "yAxis": { "domain": [0, 6400] },
  "data": [
    { "fn": "x*log(x+1)", "color": "#4a9eff", "title": "对齐，O(n log n)" },
    { "fn": "x*x", "color": "#f472b6", "title": "分离，稠密带 O(n^2)" }
  ]
}
```

## 确定性限制并行

全局修复阶段刻意单线程；只有带处理并行，且仅当带数达到 `ParallelThreshold`（默认 64）：

```csharp
if (!context.EnableParallelism || bands.Count < Math.Max(1, parallelThreshold))
    ...
Parallel.ForEach(bands, new ParallelOptions { CancellationToken = context.CancellationToken }, body);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:510-520`

并行改变大图的墙钟时间，但不改变总工作量。小图跳过并行，正是因为调度开销会超过两两比较本身。

## 试运行与内存

带 `DryRun` 的 `Arrange` 仍然构建、求解并测量；只有应用器不写回位置。结果是放置列表与代价报告。工作内存为状态数组 $O(n + e)$，瓦片索引 $O(\sum \text{触及单元})$，且每轮重建——所以峰值分配、而不只是峰值存活内存，随扫描轮数增长。
