# 表面数学

`WorkflowSurfaceMath` 是滚动、缩放与视口算术的唯一落点。`SurfaceMetrics` 是适配器每次布局时取的一份快照，推给网格装饰器、小地图与树。

## WorkflowSurfaceMath

```csharp
public static class WorkflowSurfaceMath
```

本页列出导航与视口成员。同一个类还带有网格函数（[网格数学](../../10_网格装饰器与标尺/01_网格数学/index.md)）与小地图映射函数（[小地图数学](../../09_小地图/02_小地图数学/index.md)）。

### 常量

| 常量 | 值 | 含义 |
|---|---:|---|
| `DefaultPanExtendRatio` | `0.15` | 越界时画布扩展的比例。 |

### 滚动与画布转换

| 签名 | 返回 | 说明 |
|---|---|---|
| `ToCanvasLocal(double scroll, double actualOffset)` | `double` | `scroll − actualOffset`。 |
| `ToCanvasLocalAnchor(double scrollX, double scrollY, int layer, CanvasLayout layout)` | `Anchor` | 滚动位置对应的画布局部锚点。 |
| `ToScroll(double localX, double localY, CanvasLayout layout)` | `Offset` | 画布局部点对应的滚动位置。 |
| `ScrollMax(double extent, double viewport)` | `double` | 最大可滚动偏移；下限为 0。 |
| `ClampValue(double value, double min, double max)` | `double` | 闭区间钳制。 |
| `ClampScrollOffset(double desired, double max, CanvasLayout layout, bool horizontal, double threshold = 0d, double extendRatio = 0d)` | `double` | 钳制到 `[0, max]`；把越界量写进布局的负/正偏移，并按需扩展画布。 |
| `EnsureNegativeCover(ITreeComponent? tree)` | `bool` | 内容越过原点时扩展负偏移；返回是否扩展了。 |

### 居中与缩放支点

| 签名 | 返回 | 说明 |
|---|---|---|
| `CenterScroll(double localX, double localY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | `(double ScrollX, double ScrollY)` | 把画布局部点放到视口中心所需的滚动。 |
| `ScrollCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight)` | `(double X, double Y)` | 当前位于视口中心的画布局部点。 |
| `WorldAtViewportCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | `(double WorldX, double WorldY)` | 视口中心下的世界点。 |
| `PivotCenterScroll(double pivotX, double pivotY, CanvasLayout layout, double viewportWidth, double viewportHeight)` | `(double X, double Y)` | 缩放变化后仍让支点留在视口中心的滚动。 |
| `LayoutPivot(CanvasLayout layout)` | `Anchor` | 折叠支点；视口中心模式下为 `(0,0,0)`。 |
| `ScaleCollapse(double anchorX, double anchorY, double scaleX, double scaleY)` | `(double ScaleX, double ScaleY, double CenterX, double CenterY)` | 围绕锚点的折叠变换。 |
| `ScaleVisualBounds(double anchorX, double anchorY, double width, double height, double scaleX, double scaleY)` | `(double Left, double Top, double Width, double Height)` | 围绕锚点缩放后的边界。 |

### 插槽锚点构建

| 签名 | 返回 | 说明 |
|---|---|---|
| `SlotAnchorFromVisualCenter(double centerX, double centerY, int layer, CanvasLayout layout)` | `Anchor` | 由滚动空间中的视觉中心得到锚点。 |
| `SlotAnchorFromNode(double nodeX, double nodeY, double localX, double localY, int layer)` | `Anchor` | 由节点原点加局部偏移得到锚点。 |
| `SlotAnchorFromCanvasLocal(double centerX, double centerY, int layer)` | `Anchor` | 由画布局部中心得到锚点。 |

### 视口恢复

| 签名 | 返回 | 说明 |
|---|---|---|
| `HasViewportRestore(CanvasLayout layout)` | `bool` | `ViewportOffset` 任一轴是否超过 0.5。 |
| `ViewportRestoreScroll(CanvasLayout layout)` | `Offset` | 要恢复到的滚动。 |
| `ViewportOffsetFromScroll(double scrollX, double scrollY, CanvasLayout layout)` | `Offset` | 能复现该滚动的 `ViewportOffset`。 |

## WorkflowBounds

```csharp
public readonly struct WorkflowBounds
```

| 成员 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Left` / `Top` / `Width` / `Height` | `double` | get/init | 矩形各分量。 |
| `Right` | `double` | get | `Left + Width`。 |
| `Bottom` | `double` | get | `Top + Height`。 |
| `IsEmpty` | `bool` | get | `Width <= 0 || Height <= 0`。 |

| 静态方法 | 说明 |
|---|---|
| `FromNode(double x, double y, double w, double h)` | 由节点矩形构建。 |
| `FromNodes(IEnumerable<(double X, double Y, double W, double H)> rects)` | 多个矩形的并集。 |
| `Union(WorkflowBounds a, WorkflowBounds b)` | 并集；空操作数被忽略。 |

`WorkflowBounds` 没有相等成员，也没有运算符。比较它的字段。

## SurfaceMetrics

```csharp
public readonly struct SurfaceMetrics
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 滚动容器偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 画布 `ActualOffset` 分量。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 可见视口尺寸。 |
| `RulerBand` | `double` | 覆盖上/左边缘的标尺带厚度。 |
| `VerticalScrollBarThickness` / `HorizontalScrollBarThickness` | `double` | 滚动条厚度；隐藏时为 0。 |
| `Available` | `SurfaceAvailableArea` | 覆盖层可用的空角。 |

```csharp
public static SurfaceMetrics Create(
    double scrollOffsetX, double scrollOffsetY,
    double contentOffsetX, double contentOffsetY,
    double viewportWidth, double viewportHeight,
    double surfaceWidth, double surfaceHeight,
    double rulerBand,
    double verticalScrollBarThickness, double horizontalScrollBarThickness,
    double margin);
```

`Create` 推导 `Available`：`Right = max(0, surfaceWidth − verticalScrollBarThickness)`、`Top = max(0, rulerBand)`、`Bottom = max(0, surfaceHeight − horizontalScrollBarThickness)`、`Margin = margin`。

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Right` / `Top` / `Bottom` / `Margin` | `double` | 可用角的边缘与间距。 |
| `IsUsable` | `bool` | `Right > 0 && Bottom > Top`。 |

| 方法 | 说明 |
|---|---|
| `GetRect(double desiredWidth, double desiredHeight, double minimumSize)` | 把盒子放在可用角右上，钳制到空闲区域与 `max(1, minimumSize)`；不可用时回退到 `(0,0)`。 |
| `Equals(SurfaceAvailableArea other)` | 四个 double 的值相等。 |

## SurfaceMetricsPush

```csharp
public static class SurfaceMetricsPush
```

| 签名 | 说明 |
|---|---|
| `PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree)` | 写入四个偏移，然后把树的虚拟化 inset 设为 `decorator.RulerBand`（左与上）。装饰器为 null 时抛 `ArgumentNullException`。 |
| `PushMinimap(SurfaceMetrics metrics, IWorkflowMinimapOverlay minimap, ITreeComponent? tree)` | 写入偏移、视口尺寸、树、角边缘与间距。小地图为 null 时抛 `ArgumentNullException`。 |
| `PushViewport(SurfaceMetrics metrics, ITreeComponent tree)` | 设置 `tree.GetHelper().Viewport` 并持久化 `tree.Layout.ViewportOffset`。树为 null 时抛 `ArgumentNullException`。 |

`PushViewport` 把一次滚动变成一次虚拟化。网格与小地图推送在同一次布局中随后执行。

## ISurfaceMetricsSource

```csharp
public interface ISurfaceMetricsSource
{
    SurfaceMetrics ReadMetrics();
}
```

由能够按需产出快照的适配器实现。表面行为每次布局/滚动时读取一次。
