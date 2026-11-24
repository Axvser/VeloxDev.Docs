# WinForms适配器

WinForms 是唯一不做强制布局的适配器：滚动交给 Easel 的外部滚动模型，所以平移是一次滚动请求而不是布局刷新。绘制是逐连线即时 GDI+，其特色优化是连线自带损坏矩形，重绘被裁剪到“旧曲线 ∪ 新曲线”的范围，而不是整个表面。

## 代价模型

| 符号 | 含义 |
|---|---|
| $v$ | 已实现的连线视图数 |
| $p$ | 曲线采样数（128） |
| $r$ | 可见网格线与刻度数 |
| $n$ | 节点数 |
| $A$ | 损坏面积 |
| $L$ | 布局树规模 |

## 连线渲染

生成的连线视图先算控制点、记录失效包围盒、构造 128 点曲线并发布，然后每次渲染分配 `GraphicsPath` 与 `Pen`（`Src/Templates/VeloxDev.WinForms.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:160-185`）。

```csharp
protected override void OnRender(Graphics graphics)
{
    if (!CanRender || DataContext is not ILinkComponent link || !link.IsRenderReady())
    {
        return;
    }

    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, MinimumPull);
    var drawnMinX = points.Min(point => point.X);
    var drawnMinY = points.Min(point => point.Y);
    var drawnMaxX = points.Max(point => point.X);
    var drawnMaxY = points.Max(point => point.Y);
    _lastInvalidationBounds = RectangleF.FromLTRB((float)drawnMinX, (float)drawnMinY, (float)drawnMaxX, (float)drawnMaxY);
    _lastInvalidationBounds.Inflate(12f, 12f);

    var curve = LinkCurve.FromCubic(
        points[0].X, points[0].Y, points[1].X, points[1].Y,
        points[2].X, points[2].Y, points[3].X, points[3].Y);
    link.PublishCurve(curve, this);

    using var path = new GraphicsPath();
    path.AddBezier(
        (float)points[0].X, (float)points[0].Y,
        (float)points[1].X, (float)points[1].Y,
        (float)points[2].X, (float)points[2].Y,
        (float)points[3].X, (float)points[3].Y);
```

每条可见连线的渲染是 $O(p)$ 加两个 GDI+ 对象。曲线被采样两次 —— 一次给失效盒、一次给命中测试 —— 所以常数比“单遍采样”更大。

## 基于损坏区域的重绘

`GetInvalidationBounds` 把上一次的损坏矩形与本次求并，因此局部重绘不会留下旧线段（`TemplateClass.xaml.cs:136-144`）。

```csharp
// A partial repaint clipped to the NEW curve leaves the previous segment stale ...
if (_lastInvalidationBounds.Width > 0f && _lastInvalidationBounds.Height > 0f)
{
    bounds = RectangleF.Union(bounds, _lastInvalidationBounds);
}
return bounds;
```

因此绘制代价是

$$
T_{\text{repaint}} = O(A)
$$

其中 $A$ 是损坏面积，而不是 $O(\text{表面})$。该连线用 `UnboundedHitTest = true` 退出 Easel 的损坏剔除，所以即使缓存包围盒看起来过冷，它仍会被纳入绘制考虑。

## 小地图

`DrawMinimap` 为节点分配一个 `SolidBrush`、为视口分配一个 `Pen`，设置裁剪，然后为每个映射节点填一个矩形（`Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:251-294`）。每次提交是 $O(n)$，GDI+ 对象数是常数，不是每节点一个。

## 网格

生成的网格装饰器每次渲染分配三支画笔和一个背景画刷，然后画 $O(r)$ 条线；标尺部分再加刻度画笔与每个主标签一次 `DrawString`（`Src/Templates/VeloxDev.WinForms.Templates/working/content/workflow-grid-decorator/TemplateClass.cs:283-300`）。与小地图不同，这些画笔不跨帧缓存，所以持续平移会在每次绘制时重付分配。

## 表面与滚动

表面行为中没有任何 `UpdateLayout` 调用；滚动通过 `IsExternalScroll` 与 `ScrollOffsetRequested` 委托给 `VisualScrollViewer`（`Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:495`、`:526-539`）。

$$
T_{\text{pan}} = O(1)
$$

外加 Easel 自身的失效。唯一超线性的结构代价是 z 序插入：挂接新建视图前会扫描现有子元素（`ViewContainer.cs:126-149`），所以首次物化大量视图的最坏情况是 $O(v^2)$。

## 缓存小结

- 损坏矩形求并，使重绘与变化面积成正比。
- 小地图共享一个节点画刷与一个视口画笔。
- 外部滚动完全避免布局刷新。
- 连线几何与画笔不跨渲染缓存。
- 网格画笔每次绘制重新分配。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [WinUI适配器](../27_WinUI适配器/index.md) —— 保留元素的另一条路线。
