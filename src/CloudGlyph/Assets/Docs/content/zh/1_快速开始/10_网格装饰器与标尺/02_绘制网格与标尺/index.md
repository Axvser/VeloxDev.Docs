# 绘制网格与标尺

装饰器画两层。底层填满表面并画满视口的画布网格；内容（滚动容器与画布）作为子元素夹在两层之间；顶层画半透明标尺带与刻度。不顾偏移直接画网格，只有在下一次平移之前看着对。

## 四个公式

全部网格算术都在 `WorkflowSurfaceMath`。用它，不要在每个装饰器里重推减法。

| 调用 | 公式 | 用途 |
|---|---|---|
| `GridCanvasLeft(scrollOffset, contentOffset)` | `scroll − content` | 可见画布局部区域的左边界。 |
| `GridCanvasTop(scrollOffset, contentOffset)` | `scroll − content` | 可见画布局部区域的上边界。 |
| `GridFirstLine(localLeft, spacing)` | `⌊localLeft / spacing⌋ · spacing` | 可见边界处或下方第一条网格线。 |
| `GridX(localValue, localLeft, contentRectX)` | `contentRectX + (localValue − localLeft)` | 画布局部值换算成装饰器里的 x。 |
| `GridY(localValue, localTop, contentRectY)` | `contentRectY + (localValue − localTop)` | 画布局部值换算成装饰器里的 y。 |

`contentRectX` 在浮动带模型里就是标尺厚度：网格从左侧带之后、顶部带之后开始。

## 画网格

```csharp
protected override void OnRender(DrawingContext context)
{
    var bounds = new Rect(RenderSize);
    if (bounds.Width <= 0 || bounds.Height <= 0) return;

    context.DrawRectangle(SurfaceBackgroundBrush, null, bounds);

    var ruler = Math.Max(0, owner.RulerThickness);
    var spacing = Math.Max(8, owner.GridSpacing);
    var majorStep = spacing * Math.Max(1, owner.MajorLineEvery);

    var worldLeft = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
    var worldTop = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);
    var worldRight = worldLeft + bounds.Width;
    var worldBottom = worldTop + bounds.Height;

    var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
    for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
    {
        var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
        var pen = IsNearZero(value) ? AxisPen
            : IsMajorLine(value, majorStep) ? MajorGridPen
            : MinorGridPen;
        context.DrawLine(pen, new Point(x, 0), new Point(x, bounds.Height));
    }

    var firstHorizontal = WorkflowSurfaceMath.GridFirstLine(worldTop, spacing);
    for (var value = firstHorizontal; value <= worldBottom + spacing; value += spacing)
    {
        var y = WorkflowSurfaceMath.GridY(value, worldTop, ruler);
        var pen = IsNearZero(value) ? AxisPen
            : IsMajorLine(value, majorStep) ? MajorGridPen
            : MinorGridPen;
        context.DrawLine(pen, new Point(0, y), new Point(bounds.Width, y));
    }
}
```

`IsMajorLine(value, majorStep)` 把 `value % majorStep` 与 `0`、`±majorStep` 按 epsilon（`0.001`）比较。直接 `== 0` 会因浮点累积而漏掉第一条之后的每一条线。

## 画标尺

顶层画两条带，并为穿过可见区域的每条网格线画一个刻度。主线刻度更长并带标签。

```csharp
var ruler = Math.Max(0, owner.RulerThickness);
context.DrawRectangle(RulerBackgroundBrush, null, new Rect(0, 0, bounds.Width, ruler));
context.DrawRectangle(RulerBackgroundBrush, null, new Rect(0, 0, ruler, bounds.Height));

context.DrawLine(DividerPen, new Point(ruler, 0), new Point(ruler, bounds.Height));
context.DrawLine(DividerPen, new Point(0, ruler), new Point(bounds.Width, ruler));

var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    if (x < ruler) continue;                       // skip the corner where the bands overlap

    var isMajor = IsMajorLine(value, majorStep);
    var tickLength = isMajor ? ruler - 6 : Math.Max(6, ruler * 0.35);
    context.DrawLine(TickPen, new Point(x, ruler), new Point(x, ruler - tickLength));

    if (isMajor)
    {
        DrawLabel(context, value, new Point(x + 3, 2));
    }
}
```

左侧标尺用 `GridY` 与 `GridFirstLine(worldTop, spacing)` 镜像同样步骤。

## 分层与失效

- 网格层在内容之下；`IsHitTestVisible` 为 `false`。
- 标尺层在内容之上；它同样 `IsHitTestVisible = false`，点击穿透到下面的画布。
- 装饰器自身没有背景；底层负责画表面颜色。
- 任何偏移、`RulerThickness`、`GridSpacing`、`MajorLineEvery` 变化时让两层失效，`SizeChanged` 时也失效。少了 `SizeChanged`，首次布局什么也不画。

## 预期结果

- 细线每 `GridSpacing`（默认 40）一条，粗线每 `MajorLineEvery × GridSpacing`（默认 200）一条。
- 原点两条线比其余更亮。
- 标尺标签显示网格坐标，不是屏幕坐标。
- 平移时线精确移动滚动增量；缩放不改变网格的像素间距。
- 从标尺上点击会命中画布，不是标尺。

## 下一页

[验证](../03_验证/index.md)给出完整装饰器与宿主标记。
