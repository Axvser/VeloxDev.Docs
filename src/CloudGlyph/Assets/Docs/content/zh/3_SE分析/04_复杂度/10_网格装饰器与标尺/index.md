# 网格装饰器与标尺

网格以线带绘制，而不是逐单元矩形。这改变了渐近代价：一个有 $c$ 个单元的视口，每列只需一条竖线、每行只需一条横线，所以代价与单元数的平方根成正比。标尺复用同样的间距与循环边界，只在主刻度上增加一个标签。

记号：视口宽高 $W$、$H$，网格间距 $s$，`MajorLineEvery` 为 $m$，列数 $c_w = W/s$，行数 $c_h = H/s$，可见单元 $c = c_w c_h$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| 网格层渲染 | $O(c_w + c_h)$ | $O(c_w + c_h)$ 次绘制 | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:161` |
| 标尺层渲染 | $O(c_w + c_h) + O((c_w + c_h)/m)$ 个标签 | $O(c_w + c_h)$ 个刻度 | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:194` |
| 整层重绘 | 两倍 $O(c_w + c_h)$ | — | 两层同时失效 |
| `IsMajorLine` | $O(1)$ | — | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:275` |
| 偏移映射 | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:187` |
| 首条可见线 | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:216` |
| Razor 刻度窗口重建 | 每次重建 $O(3(c_w + c_h))$ | $O(c_w + c_h)$ 个 DOM 节点 | `Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/WorkflowGridDecorator.razor.cs:180` |

## 每列一条线，每行一条线

网格按间距递增，并在每一步绘制一条贯穿的线：

```csharp
var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    var pen = IsNearZero(value) ? AxisPen : IsMajorLine(value, majorStep) ? MajorGridPen : MinorGridPen;
    context.DrawLine(pen, new Point(x, 0), new Point(x, bounds.Height));
}
```

出处：`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:171-177`

横向循环是镜像。默认 $s = 40$、$m = 5$ 时，每 200 世界单位出现一条主线。上界为：

$$
T_{\text{grid}}(W,H) = O\!\left(\frac{W}{s} + \frac{H}{s}\right) = O(c_w + c_h)
$$

而不是 $O(c)$。逐单元设计会绘制 $c_w c_h$ 个矩形，对视口尺寸呈二次。

```plot
{
  "title": "网格代价：线带与逐单元矩形",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 2500] },
  "data": [
    { "fn": "2*x", "color": "#4a9eff", "title": "O(W/s + H/s)，线带" },
    { "fn": "x*x", "color": "#f472b6", "title": "O(c)，逐单元矩形" }
  ]
}
```

## 标尺复用同一循环

标尺层遍历同样的值，跳过带内部分，并按是否主刻度决定刻度长度：

```csharp
var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    if (x < ruler) { continue; }
    var isMajor = IsMajorLine(value, majorStep);
    var tickLength = isMajor ? ruler - 6 : Math.Max(6, ruler * 0.35);
```

出处：`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:217-227`

只有主刻度才格式化标签，所以标签代价是 $O((c_w + c_h)/m)$。任何偏移或间距变更都会让两层一起失效，这就是整层重绘是单层上界两倍的原因。

## 偏移数学是常数时间

世界到局部的映射是算术；唯一稍复杂的是从可见边缘处或以下的第一条线开始：

```csharp
public static double GridCanvasLeft(double scrollOffset, double contentOffset) => scrollOffset - contentOffset;
...
public static double GridFirstLine(double localLeft, double spacing) => Math.Floor(localLeft / spacing) * spacing;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:187-217`

滚动只改变循环相位，不改变迭代次数，所以滚动帧与普通网格帧同价。

## 空间与 Razor 变体

WPF 风格实现不保留集合：其空间是保留到下一次渲染的绘制指令与格式化标签。Razor 适配器无法使用立即模式绘制，于是把刻度节点物化在三个视口宽的窗口里，只在可见范围离开内半页边距时重建。这把无界 DOM 转为 $O(3(c_w + c_h))$ 个节点，并摊平为每平移一个视口重建一次；每帧的 CSS 平移是 $O(1)$。
