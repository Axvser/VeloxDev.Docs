# WinUI适配器

WinUI 为保留式 UI 元素付出的代价大于绘制本身。小地图在视觉树里为每个节点保留一个 `Rectangle`，视图排列器为每个已实现视图订阅一个属性处理器。两者都随条目数增长；每帧绘制反而便宜，因为连线几何是原地修改的。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 节点数 |
| $v$ | 已实现视图数（节点与连线） |
| $p$ | 曲线采样数（128） |
| $L$ | 布局树规模 |
| $h$ | 每次布局突发的调度跳数 |

## 逐条目布局跟踪

`ViewLayoutTracker` 订阅每个视图条目的属性变化，并在 `Anchor`、`Size`、发送/接收或插槽变化时重新排列（`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/ViewHosting/ViewLayoutTracker.cs:28-53`）。

```csharp
PropertyChangedEventHandler handler = (_, e) =>
{
    if (!IsLayoutProperty(e.PropertyName)) return;
    var dispatcher = view.DispatcherQueue;
    if (dispatcher is null || dispatcher.HasThreadAccess) { arrange(view, item); return; }
    dispatcher.TryEnqueue(DispatcherQueuePriority.Low, () =>
    {
        if (_entries.TryGetValue(view, out var current) && ReferenceEquals(current.Source, item))
            arrange(view, item);
    });
};
notify.PropertyChanged += handler;
_entries[view] = new Entry(notify, handler);
```

$$
T_{\text{track}} = O(1) \text{（每次变化）} + O(h) \text{ 次调度跳}, \qquad S = O(v)
$$

条目字典是索引，所以取消订阅是 $O(1)$；代价在于保留的处理器与调度跳，而不是扫描。因此一批布局写入可能是每个变化视图一跳，不过重绑定检查会丢弃那些已被回收的视图的跳。

## 连线视图：原地修改几何

生成的连线视图缓存 `Path`、`PathGeometry`、`PathFigure` 与 `BezierSegment`，并原地修改段点而不重新分配（`Src/Templates/VeloxDev.WinUI.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:295-311`）。

```csharp
_path.Data = _pathGeometry;
...
private void BuildCurve(double ox, double oy)
{
    var link = DataContext as ILinkComponent;
    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, 40);
    _pathFigure.StartPoint = new Point(points[0].X + ox, points[0].Y + oy);
    _segment.Point1 = new Point(points[1].X + ox, points[1].Y + oy);
    ...
    _curve = LinkCurve.BuildLinkCubic(link, StartLeft, StartTop, EndLeft, EndTop, 40);
    PublishCurve();
}
```

曲线仍然每次更新重建，每条变化的连线 $O(p)$，但不再创建 `PathGeometry` 对象。端点属性变化同步重绘，避免连线滞后一帧；布局驱动的更新在普通调度优先级上合并。

## 小地图：每节点一个元素

小地图用池化的 `Rectangle` 子元素，而不是即时绘制。它把池增长到节点数，并把多余矩形隐藏（`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:527-551`）。

```csharp
while (_nodeRects.Count < context.MappedNodes.Count)
{
    var rect = new Rectangle();
    _nodeRects.Add(rect);
    Children.Add(rect);
}
for (int i = 0; i < _nodeRects.Count; i++)
{
    var rect = _nodeRects[i];
    if (i < context.MappedNodes.Count)
    {
        var node = context.MappedNodes[i];
        SetLeft(rect, offsetX + node.Left); SetTop(rect, offsetY + node.Top);
        rect.Width = node.Width; rect.Height = node.Height;
        rect.Fill = NodeBrush; rect.Visibility = Visibility.Visible;
```

每次绘制的代价是 $O(n)$ 次属性写入；视觉树即使隐藏也保留 $O(n)$ 个元素。相比即时模式小地图，这是更重的每节点稳态，换来更廉价的失效路径。

## 表面变换

越界与缩放沿用与 WPF 相同的三遍布局刷新（`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:772-793`、`:884-888`）。每次输入的代价在刷新时为 $O(L)$，否则 $O(1)$。

## 缓存

- 几何对象复用并原地修改，不重新分配。
- 布局更新经调度器合并。
- 小地图矩形池化，只做隐藏。
- 插槽测量使用 `LayoutUpdated` 而不是轮询。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [WinForms适配器](../29_WinForms适配器/index.md) —— 相反的选择：即时绘制加损坏矩形。
