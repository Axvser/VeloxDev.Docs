# Jalium适配器

Jalium 在绘制前按布局盒剔除子元素，所以连线视图必须先把自己的盒子移动并调整到曲线范围上，才能渲染。这次额外的重定位是本适配器的特色代价：每次刷新都要算曲线包围盒、写四个布局属性并让布局失效，此外还有常规的采样曲线。

## 代价模型

| 符号 | 含义 |
|---|---|
| $v$ | 已实现的连线视图数 |
| $p$ | 曲线采样数（128） |
| $q$ | 单条连线的控制点数（4） |
| $n$ | 节点数 |
| $r$ | 可见网格线数 |
| $L$ | 布局树规模 |

## 布局盒重定位

`WorkflowLinkBounds.Apply` 扫描点表求最小/最大值，按内边距扩展，然后写入 `Canvas.Left`、`Canvas.Top`、`Width` 与 `Height`（`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowLinkBounds.cs:58-101`）。

```csharp
foreach (var point in canvasLocalPoints)
{
    if (point.X < minX) minX = point.X;
    if (point.Y < minY) minY = point.Y;
    if (point.X > maxX) maxX = point.X;
    if (point.Y > maxY) maxY = point.Y;
}
var left = minX - BoxPad; var top = minY - BoxPad;
var right = maxX + BoxPad; var bottom = maxY + BoxPad;
originX = left; originY = top;
Canvas.SetLeft(view, left); Canvas.SetTop(view, top);
view.Width = Math.Max(1d, right - left);
view.Height = Math.Max(1d, bottom - top);
```

$$
T_{\text{relocate}} = O(q) + O(1) \text{ 次布局写入}
$$

四个控制点的扫描本身微不足道；代价在于盒子一改就让该视图的布局失效。平台按盒子剔除，所以即使绘制方已经知道曲线，这一步也省不掉。

## 连线刷新

`Refresh` 清空点表、重建、应用盒子并让视觉失效；`ScheduleRefresh` 在渲染调度优先级上合并（`Src/Templates/VeloxDev.Jalium.Templates/working/content/workflow-link-view/TemplateClass.jalxaml.cs:230-260`）。

```csharp
private void Refresh()
{
    _curve.Clear();
    _hasBounds = false;

    if (!CanRender || _link is not { } link || !link.IsVisible || !link.IsRenderReady())
    {
        InvalidateVisual();
        return;
    }

    // Bound values may be NaN before the slots are measured.
    if (double.IsNaN(StartLeft) || double.IsNaN(StartTop) || double.IsNaN(EndLeft) || double.IsNaN(EndTop))
    {
        InvalidateVisual();
        return;
    }

    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, MinimumPull);
    if (points.Length < 4)
    {
        InvalidateVisual();
        return;
    }

    // Size the box to all four control points; the endpoints alone clip the curve's bulge.
    foreach (var (x, y) in points)
    {
        _curve.Add(new Point(x, y));
    }

    _hasBounds = WorkflowLinkBounds.Apply(this, _curve, out _originX, out _originY);
    InvalidateVisual();
}
```

随后 `OnRender` 构造 `PathGeometry`、画刷与画笔，并发布 128 点曲线，所以每条失效连线的每帧代价是 $O(p)$ 加分配。

## 小地图

小地图为每个映射节点画一个圆角矩形，并在每一遍为边框和视口各分配一支新 `Pen`；WPF 与 Avalonia 会缓存它们（`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:465-490`）。

```csharp
dc.DrawRoundedRectangle(MinimapBackground, null, mmRect, cr, cr);
dc.DrawRoundedRectangle(MinimapBorderThickness > 0 ? new Pen(MinimapBorderBrush, MinimapBorderThickness) : null, ...);
foreach (var node in context.MappedNodes)
{
    dc.DrawRoundedRectangle(NodeBrush, null, new Rect(...), ncr, ncr);
}
...
if (ViewportStrokeThickness > 0)
    dc.DrawRectangle(ViewportFill, new Pen(ViewportStroke, ViewportStrokeThickness), ...);
```

每次绘制提交是 $O(n)$，另加两次画笔分配。映射只在管线变脏时重算。

## 表面变换

世界位移以 `TranslateTransform` 附加属性发布到宿主；节点与连线模板把它绑定到自己的 `RenderTransform`（`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:841-845`）。越界与缩放调用 `EnsureNegativeCover`，并在十三处刷新布局（`:658-702`、`:1414-1419`）。

$$
T_{\text{pan}} = O(1) + \begin{cases} 0 & \text{布局未变} \\ O(L) & \text{刷新布局} \end{cases}
$$

## 缓存小结

- `_refreshPending` 在渲染优先级上合并刷新。
- `_hasBounds` 在盒子未知前跳过绘制。
- 表面变换每帧只有一次附加属性写入。
- 128 点曲线与绘制几何每次刷新重建。
- 小地图画笔每遍分配。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [WPF适配器](../25_WPF适配器/index.md) —— 类似的逐连线视图，但没有盒子重定位。
