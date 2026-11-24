# Avalonia适配器

Avalonia 闭包与 WPF 相同的角色集，但缓存了命中测试曲线。连线视图仍然每次绘制都构造 `StreamGeometry`、画刷与画笔，但 128 点曲线只在端点或数据上下文变化时刷新；表面变换的强制布局次数也少得多。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 节点数 |
| $v$ | 已实现的连线视图数 |
| $p$ | 曲线采样数（128） |
| $r$ | 可见网格线与刻度数 |
| $L$ | 布局树规模 |

## 连线视图：缓存曲线、重建几何

`RefreshGeometry` 只在 `OnPropertyChanged` 时重建 `LinkCurve.BuildLinkCubic`；`Render` 随后分配几何、画刷与画笔（`Src/Templates/VeloxDev.Avalonia.Templates/working/content/workflow-link-view/TemplateClass.axaml.cs:125-169`）。

```csharp
private void RefreshGeometry()
{
    var link = DataContext as ILinkComponent;
    _curve = LinkCurve.BuildLinkCubic(link, StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
    link?.PublishCurve(_curve, this);
}

public override void Render(DrawingContext context)
{
    ...
    var brush = new ImmutableSolidColorBrush(LineColor);
    var pen = IsVirtualLink ? new Pen(brush, LineThickness) { DashStyle = new DashStyle([4.0, 2.0], 0) } : new Pen(brush, LineThickness);
    var geometry = BuildCurve(DataContext as ILinkComponent);
    context.DrawGeometry(null, pen, geometry);
}
```

因此一次绘制的代价是

$$
T_{\text{frame}} = O(v) + O(\text{几何大小})
$$

而不是 $O(v \cdot p)$：采样表跨帧复用。端点每帧都在动（拖拽）与不动（静态缩放）时，这一差别都很关键。

```plot
{
  "title": "每帧采样工作量",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 13000] },
  "data": [
    { "fn": "128*x", "color": "#f472b6", "title": "逐连线重建曲线" },
    { "fn": "x", "color": "#4a9eff", "title": "缓存曲线" }
  ]
}
```

## 小地图

`DrawMinimap` 为每个映射节点填充一个矩形，并按画刷引用缓存视口画笔（`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:424-492`）。

```csharp
if (NodeBrush is not null)
{
    var ncr = (float)Math.Max(0, context.NodeCornerRadius);
    foreach (var node in context.MappedNodes)
    {
        drawingContext.FillRectangle(NodeBrush,
            new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr);
    }
}
```

每次绘制提交是 $O(n)$ 且无逐节点分配；映射受脏标记控制。画笔查找首次之后是 $O(1)$（`:483-491`）。

## 表面变换

枢轴与越界数学与 WPF 相同，但本适配器只有五处强制布局，而不是十六处（`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:110-147`）。常见平移路径只写入滚动偏移并更新区域；只有布局真的变化时才刷新。

$$
T_{\text{pan}} = O(1) + \begin{cases} 0 & \text{布局未变} \\ O(L) & \text{刷新布局} \end{cases}
$$

## 池与命中测试

池策略批量为 1024、帧预算 16 ms、每类型无限回收（`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/ViewHosting/ViewPoolPolicy.cs:10-19`）。$v$ 个视图的突发在 $\lceil v/1024 \rceil$ 个调度轮次内实现，而不是 $\lceil v/3 \rceil$；总量仍是 $O(v)$。

命中测试走 Core：每次指针移动 $O(d + v(1+p))$，缓存曲线让逐连线遍历不产生分配。

## 网格

生成的网格装饰器每次渲染重画可见线与刻度标签，$O(r)$，复用冻结的静态画笔。与 WPF 一样，代价随可见标尺窗口缩放，而不随图规模。

## 缓存小结

- 命中测试曲线跨绘制缓存。
- 画笔按画刷引用与线宽缓存。
- 小地图映射受脏标记控制。
- 池可吸收大批量突发。
- 绘制用的 `StreamGeometry` 仍然每次重绘重建。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [WPF适配器](../25_WPF适配器/index.md) —— 同一组角色，没有缓存曲线。
