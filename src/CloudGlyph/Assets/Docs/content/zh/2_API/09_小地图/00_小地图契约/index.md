# 小地图契约

小地图由表面行为喂数据，并由三个平台层组合而成。下面的契约就是全部交换面。

## IWorkflowMinimapOverlay

```csharp
public interface IWorkflowMinimapOverlay : IWorkflowGridDecorator
{
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    ITreeComponent? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
    double AvailableRight { get; set; }
    double AvailableTop { get; set; }
    double AvailableBottom { get; set; }
    double MinimapMargin { get; set; }
}
```

它派生自 `IWorkflowGridDecorator`，因此也带有 `ScrollOffsetX`、`ScrollOffsetY`、`ContentOffsetX`、`ContentOffsetY` 与只读的 `RulerBand`。

| 成员 | 含义 |
|---|---|
| `ViewportWidth` / `ViewportHeight` | 表面滚动空间中的视口尺寸，用于缩放指示块与解析拖动。 |
| `WorkflowTree` | 要渲染的树。 |
| `IsMinimapVisible` | 一次绘制是否画出任何东西。 |
| `AvailableRight` | 可用右边缘的 X，排除垂直滚动条。 |
| `AvailableTop` | 可用上边缘的 Y，位于标尺带之下。 |
| `AvailableBottom` | 可用下边缘的 Y，排除水平滚动条。 |
| `MinimapMargin` | 与可用角保持的间距。 |

表面行为在每次绘制前写入所有成员。小地图只读它们，宿主通常不会手写。

## IMinimapRenderer<TSurface>

```csharp
public interface IMinimapRenderer<TSurface>
{
    void Render(TSurface surface, MinimapDrawContext context);
}
```

绘制一次：边框、`context.MappedNodes` 里的每个矩形，以及 `context.MappedViewport` 里的视口指示块。默认适配器渲染器不画连线。

## IMinimapViewportHost

```csharp
public interface IMinimapViewportHost
{
    double ScrollOffsetX { get; }
    double ScrollOffsetY { get; }
    double ContentOffsetX { get; }
    double ContentOffsetY { get; }
    double ViewportWidth { get; }
    double ViewportHeight { get; }
    double ScrollableWidth { get; }
    double ScrollableHeight { get; }
    void ApplyScroll(double x, double y);
}
```

滚动空间由宿主定义。管线用 `scroll − contentOffset` 与可滚动尺寸来钳制拖动。没有原生上限的平台用哨兵值告诉管线不要钳制。

## IMinimapInputHost

```csharp
public interface IMinimapInputHost
{
    (double X, double Y) PointerPosition { get; }
    bool IsPressed { get; }
    bool IsCaptured { get; }
    WorkflowBounds ClampRect { get; }
    bool Capture();
    void Release();
}
```

| 成员 | 含义 |
|---|---|
| `PointerPosition` | 覆盖层局部指针位置。 |
| `IsPressed` | 主键是否按下。 |
| `IsCaptured` | 平台是否捕获了指针。 |
| `ClampRect` | 可选命中矩形；为空时管线使用自己放置的矩形。 |
| `Capture()` | 捕获指针；返回是否成功。 |
| `Release()` | 释放捕获。 |

## MinimapMetrics

```csharp
public readonly struct MinimapMetrics : IEquatable<MinimapMetrics>
```

| 成员 | 类型 | 默认 | 含义 |
|---|---|---:|---|
| `Width` | `double` | `200d` | 钳制前的请求宽度。 |
| `Height` | `double` | `140d` | 钳制前的请求高度。 |
| `Available` | `SurfaceAvailableArea` | 间距 12 | 可用角。 |
| `MinSize` | `double` | `20d` | 最小宽高。 |
| `Padding` | `double` | `2d` | 映射内容四周的内边距。 |
| `NodeCornerRadius` | `double` | `1d` | 缩略块圆角。 |
| `MinimapCornerRadius` | `double` | `4d` | 边框圆角。 |
| `MinimumThumbSize` | `double` | `2d` | 最小缩略块边长。 |
| `Default` | `static MinimapMetrics` | — | 上述默认值。 |

`Equals(MinimapMetrics)` 比较每个放置输入，因此未变的 metrics 不会触发重映射。

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
{
    public double Right { get; init; }
    public double Top { get; init; }
    public double Bottom { get; init; }
    public double Margin { get; init; }
    public bool IsUsable { get; }
    public WorkflowBounds GetRect(double desiredWidth, double desiredHeight, double minimumSize);
    public bool Equals(SurfaceAvailableArea other);
}
```

`GetRect` 把请求的盒子放在角的右上，钳制到空闲区域与 `max(1, minimumSize)`；区域不可用时回退到 `(0,0)`。完整说明（含 `SurfaceMetrics.Available`）见[表面数学](../../07_画布输入与导航/03_表面数学/index.md)。

## 说明

- 本组里只有 `IWorkflowMinimapOverlay` 由表面行为写入；其余接口由适配器的管线实现。
- `MinimapMetrics` 是值类型；赋一个新值，而不是修改副本。
- `MinimumThumbSize` 防止远处节点完全消失。
