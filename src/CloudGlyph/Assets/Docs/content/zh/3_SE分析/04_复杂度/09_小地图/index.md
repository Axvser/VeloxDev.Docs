# 小地图

小地图是整份文档的缩略图：它映射树中的每个节点，而不只是可见节点。这条路径上没有空间索引，也没有连线层。因此一次重映射对节点数线性，而任何把小地图标脏的变更都会在下一次渲染时付出这个线性代价。

记号：$n$ 个节点，$m$ 条连线，主视口中可见的 $v$ 个节点。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `BuildDrawContext` | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:294` |
| `Refresh`，未标脏 | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:175` |
| `Render`（无论是否标脏） | $O(n)$ | $O(n)$ 绘制指令 | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:188` |
| `HitTest` / `MinimapRect` | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:208` |
| `PointerPressed` | 标脏时 $O(n)$，否则 $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:215` |
| `PointerMoved` 拖拽映射 | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:236` |
| 订阅 / 取消订阅 | $O(n + m)$ | $O(n + m)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:413` |
| 节点 / 连线集合变更 | $O(k)$，重置时 $O(n)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:544` |

## 每次重映射三次线性遍历

内容包围盒、节点矩形与映射矩形各由一次整节点列表遍历构建：

```csharp
var nodeRects = new List<(double X, double Y, double W, double H)>(tree.Nodes.Count);
foreach (var node in tree.Nodes)
{
    nodeRects.Add((node.Anchor.Horizontal, node.Anchor.Vertical, node.Size.Width, node.Size.Height));
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:303-307`

```csharp
foreach (var (nx, ny, nw, nh) in nodeRects)
{
    nodes.Add(WorkflowBounds.FromNode(nx, ny, nw, nh));
    var (l, t) = WorkflowSurfaceMath.MinimapLocal(nx, ny, ContentBounds.Left, ContentBounds.Top, ox, oy, sc);
    mapped.Add(WorkflowBounds.FromNode(l, t,
        WorkflowSurfaceMath.MinThumbSize(nw, sc, minThumb),
        WorkflowSurfaceMath.MinThumbSize(nh, sc, minThumb)));
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:334-343`

重映射是 $O(n)$，与 $v$ 无关。渲染器随后遍历每个映射节点：

```csharp
foreach (var node in context.MappedNodes)
{
    dc.DrawRoundedRectangle(NodeBrush, null,
        new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr, ncr);
}
```

出处：`Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:421-425`

```plot
{
  "title": "小地图代价：全部节点与仅视口",
  "grid": true,
  "xAxis": { "domain": [0, 200] },
  "yAxis": { "domain": [0, 200] },
  "data": [
    { "fn": "x", "color": "#f472b6", "title": "实际：每次重映射 O(n)" },
    { "fn": "10", "color": "#4a9eff", "title": "若按视口设计则为 O(v)" }
  ]
}
```

## 脏标记摊平代价

节点属性变更只在 `Anchor` 与 `Size` 上把小地图标脏；成批变更合并为一个标志，`Refresh` 在未标脏时提前返回。拖动小地图本身复用缓存上下文，只重算滚动映射，因此拖拽每次指针移动 $O(1)$。代价落在适配器侧：主画布滚动会推送度量，使流水线失效，于是下一次渲染重建完整的 $O(n)$ 映射，即使只有视口矩形变了。

## 这里没有什么

小地图不携带连线列表，所以没有适配器在缩略图中画连线。它也不查询 `WorkflowSpatialManager`；节点遍历是直接的。内存是保留到下一次重映射的 $O(n)$ 个映射矩形，加上用于脏跟踪的 $O(n + m)$ 个实时事件订阅。
