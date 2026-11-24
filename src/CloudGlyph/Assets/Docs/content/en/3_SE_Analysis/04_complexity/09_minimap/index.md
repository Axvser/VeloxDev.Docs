# Minimap

The minimap is a full-document thumbnail: it maps every node in the tree, not only the visible ones. There is no spatial index on this path and no link layer. A remap is therefore linear in the node count, and any change that marks the pipeline dirty pays that linear cost on the next render.

Notation: $n$ nodes, $m$ links, $v$ nodes visible in the main viewport.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `BuildDrawContext` | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:294` |
| `Refresh` when clean | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:175` |
| `Render` (dirty or clean) | $O(n)$ | $O(n)$ drawing instructions | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:188` |
| `HitTest` / `MinimapRect` | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:208` |
| `PointerPressed` | $O(n)$ if dirty, else $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:215` |
| `PointerMoved` drag mapping | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:236` |
| Subscribe / unsubscribe | $O(n + m)$ | $O(n + m)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:413` |
| Node/link collection change | $O(k)$, $O(n)$ on reset | — | `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:544` |

## Three linear passes per remap

Content bounds, node rectangles, and mapped rectangles are each built by walking the whole node list:

```csharp
var nodeRects = new List<(double X, double Y, double W, double H)>(tree.Nodes.Count);
foreach (var node in tree.Nodes)
{
    nodeRects.Add((node.Anchor.Horizontal, node.Anchor.Vertical, node.Size.Width, node.Size.Height));
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:303-307`

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

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs:334-343`

The remap is $O(n)$ and independent of $v$. The renderer then loops over every mapped node:

```csharp
foreach (var node in context.MappedNodes)
{
    dc.DrawRoundedRectangle(NodeBrush, null,
        new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr, ncr);
}
```

Source: `Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:421-425`

```plot
{
  "title": "Minimap cost: all nodes vs viewport only",
  "grid": true,
  "xAxis": { "domain": [0, 200] },
  "yAxis": { "domain": [0, 200] },
  "data": [
    { "fn": "x", "color": "#f472b6", "title": "actual: O(n) every remap" },
    { "fn": "10", "color": "#4a9eff", "title": "a viewport-bound design would be O(v)" }
  ]
}
```

## Dirty tracking amortizes the cost

A node property change marks the pipeline dirty only for `Anchor` and `Size`; bursts of changes coalesce into one flag, and `Refresh` early-returns when clean. Dragging the minimap itself reuses the cached context and only recomputes the scroll mapping, so the drag is $O(1)$ per pointer move. The catch is on the adapter side: a main-canvas scroll pushes metrics, which invalidates the pipeline, so the next render rebuilds the full $O(n)$ mapping even though only the viewport rectangle changed.

## What is not here

The minimap carries no link list, so no adapter draws links in the thumbnail. It also does not consult `WorkflowSpatialManager`; the node walk is direct. Memory is $O(n)$ mapped rectangles retained until the next remap, plus $O(n + m)$ live event subscriptions for dirty tracking.
