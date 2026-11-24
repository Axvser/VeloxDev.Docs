# 表面数学

`WorkflowSurfaceMath` 是各适配器共享的坐标与钳制算术。滚动偏移、画布内容偏移、画布局部位置和视口矩形都在这里换算，而不是在每个平台各写一遍。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## WorkflowSurfaceMath

**签名：** `static class WorkflowSurfaceMath`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `DefaultPanExtendRatio` | `const double`（`0.15`） | 平移越界时画布增长占视口的比例。 |
| `ToCanvasLocal` | `static double ToCanvasLocal(double scroll, double actualOffset)` | `local = scroll − contentOffset`。 |
| `ToCanvasLocalAnchor` | `static Anchor ToCanvasLocalAnchor(double scrollX, double scrollY, int layer, CanvasLayout layout)` | 滚动位置转画布局部锚点。 |
| `ToScroll` | `static Offset ToScroll(double localX, double localY, CanvasLayout layout)` | 画布局部点转滚动偏移。 |
| `HasViewportRestore` | `static bool HasViewportRestore(CanvasLayout layout)` | 布局是否携带已保存且非零的视口位置。 |
| `ViewportRestoreScroll` | `static Offset ViewportRestoreScroll(CanvasLayout layout)` | 要恢复的已保存滚动位置。 |
| `ViewportOffsetFromScroll` | `static Offset ViewportOffsetFromScroll(double scrollX, double scrollY, CanvasLayout layout)` | 滚动偏移转持久化到 `Layout.ViewportOffset` 的值。 |
| `ClampScrollOffset` | `static double ClampScrollOffset(double desired, double max, CanvasLayout layout, bool horizontal, double threshold = 0d, double extendRatio = 0d)` | 钳制偏移；越界时按比例扩张画布。 |
| `ScrollMax` | `static double ScrollMax(double extent, double viewport)` | 给定范围与视口的最大偏移。 |
| `ClampValue` | `static double ClampValue(double value, double min, double max)` | 常规钳制。 |
| `GridCanvasLeft` / `GridCanvasTop` | `static double GridCanvasLeft(double scrollOffset, double contentOffset)` / `static double GridCanvasTop(double scrollOffset, double contentOffset)` | 网格层的画布原点。 |
| `GridX` / `GridY` | `static double GridX(double localValue, double localLeft, double contentRectX)` / `static double GridY(double localValue, double localTop, double contentRectY)` | 网格线位置。 |
| `GridFirstLine` | `static double GridFirstLine(double localLeft, double spacing)` | 可见边缘之后的第一条网格线。 |
| `SlotAnchorFromVisualCenter` | `static Anchor SlotAnchorFromVisualCenter(double centerX, double centerY, int layer, CanvasLayout layout)` | 由视觉中心得到锚点。 |
| `SlotAnchorFromNode` | `static Anchor SlotAnchorFromNode(double nodeX, double nodeY, double localX, double localY, int layer)` | 由节点局部点得到锚点。 |
| `SlotAnchorFromCanvasLocal` | `static Anchor SlotAnchorFromCanvasLocal(double centerX, double centerY, int layer)` | 由画布局部中心得到锚点（不再减偏移）。 |
| `MinimapFit` | `static (double OriginX, double OriginY, double Scale) MinimapFit(double contentWidth, double contentHeight, double drawWidth, double drawHeight, double padding)` | 把世界包围盒适配到小地图。 |
| `MinimapLocal` | `static (double LocalX, double LocalY) MinimapLocal(double contentX, double contentY, double contentLeft, double contentTop, double originX, double originY, double scale)` | 世界点 → 小地图局部点。 |
| `MinimapViewportRect` | `static (double X, double Y, double Width, double Height) MinimapViewportRect(double originX, double originY, double scale, double vpLeft, double vpTop, double vpWidth, double vpHeight, double contentLeft, double contentTop, double mmWidth, double mmHeight, double minRectSize)` | 小地图像素中的视口框。 |
| `MinimapToCanvasLocal` | `static (double LocalX, double LocalY) MinimapToCanvasLocal(double mmX, double mmY, double originX, double originY, double scale, double contentLeft, double contentTop)` | 小地图点 → 画布局部点。 |
| `MinimapToScroll` | `static (double ScrollX, double ScrollY) MinimapToScroll(double localX, double localY, double viewportWidth, double viewportHeight, double contentOffsetX, double contentOffsetY)` | 小地图点 → 滚动偏移。 |
| `CenterScroll` | `static (double ScrollX, double ScrollY) CenterScroll(double localX, double localY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | 使画布局部点居中的滚动偏移。 |
| `ScrollCenter` | `static (double X, double Y) ScrollCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight)` | 滚动位置对应的画布局部中心。 |
| `WorldAtViewportCenter` | `static (double WorldX, double WorldY) WorldAtViewportCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | 视口中心下的世界点。 |
| `PivotCenterScroll` | `static (double X, double Y) PivotCenterScroll(double pivotX, double pivotY, CanvasLayout layout, double viewportWidth, double viewportHeight)` | 保持缩放枢轴不动的滚动位置。 |
| `LayoutPivot` | `static Anchor LayoutPivot(CanvasLayout layout)` | 布局的缩放枢轴。 |
| `MinThumbSize` | `static double MinThumbSize(double size, double scale, double min)` | 钳制小地图缩略尺寸。 |
| `ScaleCollapse` | `static (double ScaleX, double ScaleY, double CenterX, double CenterY) ScaleCollapse(double anchorX, double anchorY, double scaleX, double scaleY)` | 为视图折叠世界缩放。 |
| `ScaleVisualBounds` | `static (double Left, double Top, double Width, double Height) ScaleVisualBounds(double anchorX, double anchorY, double width, double height, double scaleX, double scaleY)` | 缩放折叠后的视觉包围盒。 |
| `EnsureNegativeCover` | `static bool EnsureNegativeCover(ITreeComponent? tree)` | 扩张负向画布覆盖，使平移后的内容仍可寻址。 |

```csharp
var localX = WorkflowSurfaceMath.ToCanvasLocal(scrollOffsetX, layout.ActualOffset.Horizontal);
var (centerX, centerY) = WorkflowSurfaceMath.CenterScroll(
    localX: 400, localY: 300, viewportWidth: 800, viewportHeight: 600, layout);
```

**预期结果：** 滚动到 `scrollOffsetX` 的表面在每家适配器上报告相同的画布局部位置，因为减法只在这里做一次。
