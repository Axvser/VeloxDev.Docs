# WPF适配器

WPF 为每条连线绘制一个视图，小地图则即时模式绘制。反复出现的代价是连线视图的 `OnRender`：每次失效帧都重建采样曲线、几何、画刷和画笔。输入路径的大头不是绘制，而是强制布局：当平移或缩放触及滚动边界时，布局会被刷新三次。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 节点数 |
| $m$ | 连线数 |
| $v$ | 已实现的连线视图数（可见连线） |
| $p$ | 每条连线的曲线采样数（128） |
| $r$ | 可见网格线与标尺刻度数 |
| $L$ | 布局树规模 |

## 每帧连线绘制

生成的连线视图先发布命中测试曲线，然后为每次渲染构造 `PathGeometry`、`SolidColorBrush` 与 `Pen`（`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:85-104`）。

```csharp
protected override void OnRender(DrawingContext ctx)
{
    base.OnRender(ctx);
    if (!CanRender) return;
    if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

    // Publish the curve the surface hit-tests against: same control points as BuildCurve, same
    // canvas-local space. Replace this together with BuildCurve if you change the shape.
    PublishCurve(LinkCurve.BuildLinkCubic(DataContext as ILinkComponent, StartLeft, StartTop, EndLeft, EndTop, MinimumPull));

    var thickness = LineThickness;
    var geometry = BuildCurve(DataContext as ILinkComponent);

    var brush = new SolidColorBrush(LineColor);
    var pen = IsVirtualLink
        ? new Pen(brush, thickness) { DashStyle = new DashStyle(new double[] { 4, 2 }, 0) }
        : new Pen(brush, thickness);

    ctx.DrawGeometry(null, pen, geometry);
}
```

`LinkCurve` 默认采样 128 个点（`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:26`），所以一帧有 $v$ 条失效连线的代价是

$$
T_{\text{frame}} = O(v \cdot p) + O(v) \text{ 次分配}
$$

几何即使被冻结，也会在下一帧被丢弃重建。这是适配器里最贵的每帧路径；问题不在池本身。

## 小地图

`WorkflowMinimapOverlay.OnRender` 映射所有节点（不只是可见节点），并为每个映射节点提交一个圆角矩形（`Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:398-425`）。

```csharp
protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context)
{
    var bounds = context.GetMinimapRect(MinimapMinSize);
    var mmRect = new Rect(bounds.Left, bounds.Top, bounds.Width, bounds.Height);
    var offsetX = mmRect.Left;
    var offsetY = mmRect.Top;
    var cr = Math.Max(0, context.MinimapCornerRadius);

    // 缩略图背景
    if (MinimapBackground is not null)
        dc.DrawRoundedRectangle(MinimapBackground, null, mmRect, cr, cr);
    if (MinimapBorderBrush is not null)
        dc.DrawRoundedRectangle(null, GetPen(ref _borderPen, MinimapBorderBrush, MinimapBorderThickness), mmRect, cr, cr);

    if (_clipGeometry is null || _clipGeometry.Rect != mmRect)
        _clipGeometry = new RectangleGeometry(mmRect);
    dc.PushClip(_clipGeometry);
    try
    {
        // 节点
        if (NodeBrush is not null)
        {
            var ncr = Math.Max(0, context.NodeCornerRadius);
            foreach (var node in context.MappedNodes)
            {
                dc.DrawRoundedRectangle(NodeBrush, null,
                    new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr, ncr);
            }
        }
```

每次绘制提交是 $O(n)$；只有管线变脏时才重算映射。画笔与裁剪几何被缓存（`:372-383`），所以分配代价有界。

## 表面变换

缩放与平移先应用世界变换，然后在偏移触及滚动边界时先刷新布局再读取新的最大值（`Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:1260-1269`）。

```csharp
if (layoutChanged)
{
    ApplyLayout(host, state);
    state.Canvas?.UpdateLayout();
    state.ScrollViewer.UpdateLayout();
    host.UpdateLayout();
    maxH = GetHorizontalScrollMaximum(state.ScrollViewer);
    maxV = GetVerticalScrollMaximum(state.ScrollViewer);
```

$$
T_{\text{pan}} = \begin{cases} O(1) & \text{偏移被钳制} \\ O(L) & \text{刷新布局} \end{cases}
$$

该文件中有十六处 `UpdateLayout`/`Measure`/`Arrange` 调用；三遍刷新正是用户在越界滚动时能感觉到的输入代价。

## 命中测试与拖拽

`ResolveTarget` 先走视觉祖先链，再委托 Core 的连线命中测试遍历 `VisibleItems`（`WorkflowSurfaceBehavior.cs:1035-1055`；`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:76-93`）。每条连线的 `Contains` 先做包围盒排除，再逐段遍历（`LinkCurve.cs:318-336`）。

$$
T_{\text{hit}} = O(d + v(1 + p))
$$

包围盒排除让常见情况降到 $O(d + v)$。节点拖拽每次移动按祖先链解析节点，$O(d)$。

## 池与网格

视图池在 8-16 ms 帧预算下分批物化，模板查找按运行时类型缓存（`Src/Adapters/VeloxDev.WPF/WorkflowSystem/ViewHosting/ViewFactory.cs:42-78`）。排列器是空操作。生成的网格装饰器每次渲染重画所有可见线与标尺刻度，$O(r)$，每个主刻度标签一次 `FormattedText` 分配。

## 缓存

- 小地图画笔与裁剪几何复用。
- 网格模板中的静态画笔被冻结。
- 模板按运行时类型缓存。
- 连线几何被冻结，但只在重建之后；没有东西把它跨帧保留下来。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [Avalonia适配器](../26_Avalonia适配器/index.md) —— 同一组角色，命中测试曲线被缓存。
