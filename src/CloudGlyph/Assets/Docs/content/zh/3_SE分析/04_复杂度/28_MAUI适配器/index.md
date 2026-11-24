# MAUI适配器

MAUI 在单个 `GraphicsView` 里绘制所有可见连线。没有逐连线视图：一个绘制器枚举可见集合，把每条曲线重建进复用的点数组，按包围盒剔除，再对正文描边数次。流动动画引入第二个大得多的项：彗星每个尾段、每一遍都要重新采样曲线。

## 代价模型

| 符号 | 含义 |
|---|---|
| $v$ | 可见连线数 |
| $p$ | 曲线采样数（128） |
| $k$ | 彗星尾段数（16） |
| $r$ | 可见网格单元数 |
| $n$ | 节点数 |
| bytes | 媒体/负载字节数 |

## 单遍连线绘制

`LinkOverlayDrawable.Draw` 只枚举 Core 的 `VisibleItems`，所以循环量是 $v$ 而不是全部 $m$ 条连线（`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/AttachedBehaviors/WorkflowLinkOverlay.cs:1583-1654`）。

```csharp
foreach (var link in EnumerateVisibleLinks(tree))
{
    // 这条线已经有自己的视图在画（视图发布曲线时把「画它的那个控件」一并交了上来）——
    // 这层只画没人画的：立即模式的主机，以及池化视图还没物化出来的那几帧
    if (link.HitTarget()?.Visual is not null)
    {
        continue;
    }

    if (!TryGetEndpoints(link, out var csx, out var csy, out var cex, out var cey))
    {
        continue;
    }

    var isVirtual = IsVirtualLink(link);
    var color = isVirtual ? owner.VirtualColorFor(link, virtualColor) : linkColor;
    if (color is null)
    {
        continue;
    }

    var curve = LinkCurve.BuildLinkCubic(
        link, csx, csy, cex, cey, PullMinimum, LinkCurve.DefaultSampleCount);
    link.PublishCurve(curve);

    owner.BuildViewportGeometry(
        curve,
        ToViewport(ruler, ox, scrollX, 0),
        ToViewport(ruler, oy, scrollY, 0));
```

`BuildViewportGeometry` 把 128 个点复制进复用的 `PointF[]`，并原地修改复用的 `PathF`（`:363-394`）；`IntersectsViewport` 扫描同样的 128 个采样点求包围盒（`:402-419`）。两者都是每条可见连线 $O(p)$。

$$
T_{\text{frame}} = O(v \cdot p)
$$

正文描边两到四次，颜色按 alpha 档缓存，所以每条连线的分配被限制在曲线对象上。

## 流动彗星

开启流动后，`DrawComet` 对尾部做两遍循环，每个尾段都要扫描采样表来定位自己（`WorkflowLinkOverlay.cs:505-535`）。

```csharp
for (var pass = 0; pass < 2; pass++)
{
    var bloom = pass == 0;
    for (var k = 0; k < TailSegments; k++)
    {
        var f0 = k / (float)TailSegments;
        var f1 = (k + 1) / (float)TailSegments;
        var l0 = head - (tail * (1 - f0));
        var l1 = head - (tail * (1 - f1));
        ...
        var segmentColor = Mix(color, Colors.White, f0);
        canvas.StrokeColor = bloom ? Fade(segmentColor, alpha * 0.22) : Fade(segmentColor, alpha);
        canvas.StrokeSize = bloom ? thickness + 9 : thickness * (0.45f + (0.95f * f0));
        StrokeSegment(canvas, l0, l1);   // scans all 128 samples
    }
}
```

$k = 16$ 段、2 遍时，一条流动连线每帧约做 4096 次采样操作，即 $(2 \cdot 16 \cdot 128)$ 次：

$$
T_{\text{flow}} = O(v \cdot k \cdot p)
$$

当大量连线在动，这就是每帧的主导项；彗星也是本适配器不能简单归结为 $O(v \cdot p)$ 的原因。

```plot
{
  "title": "每条流动连线的彗星采样量",
  "grid": true,
  "xAxis": { "domain": [1, 32] },
  "yAxis": { "domain": [0, 9000] },
  "data": [
    { "fn": "2*128*x", "color": "#f472b6", "title": "2 遍 x 128 采样" },
    { "fn": "128", "color": "#4a9eff", "title": "仅正文" }
  ]
}
```

## 失效

每次模型或偏移变化都调用 `ScheduleInvalidate`，它把刷新合并到下一次主线程派发，再加一次补绘以捕获布局末尾写入的锚点（`WorkflowLinkOverlay.cs:1473-1503`）。一批变化只花 $O(1)$ 次失效，而不是每次变化一次。

## 小地图与网格

小地图是即时 `ICanvas` 绘制：每次提交为每个映射节点一次 `FillRoundedRectangle`，$O(n)$，且不分配画刷或画笔，因为颜色直接设在画布上（`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:713-781`）。网格装饰器用两个 `GraphicsView`，其绘制器循环可见单元，每帧 $O(r)$，外加每个主刻度的文本。

## 排列

`ViewArranger` 订阅每个视图的条目，并把包围盒写入合并到每个调度轮次一次（`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/ViewHosting/ViewArranger.cs:168-189`）。订阅开销 $O(v)$；每次变化 $O(1)$，至多一跳。

## 缓存小结

- 复用 `PointF[128]` 与 `PathF`，原地修改。
- 淡出颜色按源颜色缓存。
- 失效合并到大约每帧一次。
- 可见集合迭代避免扫描全部连线。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 本适配器消费的共享结构。
- [Razor适配器](../30_Razor适配器/index.md) —— 另一种单层连线策略，移到了 JavaScript 里。
