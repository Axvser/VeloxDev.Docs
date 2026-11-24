# 表面度量

表面每次刷新计算一份不可变快照，并把同一组数字推给网格装饰器、小地图和树的视口。把算术留在 Core，七个适配器才会以同样的方式为标尺和滚动条收缩覆盖层可用区。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## SurfaceViewport

**签名：** `sealed record SurfaceViewport(ITreeComponent Tree, double ScrollLeft, double ScrollTop, double ViewportWidth, double ViewportHeight, double ContentOffsetX, double ContentOffsetY)`

表面状态的不可变快照，交给视口驱动的覆盖层，使其无需重建整个表面即可重绘。

## SurfaceCanvas

**签名：** `sealed record SurfaceCanvas(double Width, double Height)`

计算出的画布尺寸，交给内容片段（例如 SVG 连线层），让子元素与同一画布等大。

## SurfaceMetrics

**签名：** `readonly struct SurfaceMetrics`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double`（init） | 滚动容器偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double`（init） | 画布内容偏移（`CanvasLayout.ActualOffset`）。 |
| `ViewportWidth` / `ViewportHeight` | `double`（init） | 可见视口尺寸。 |
| `RulerBand` | `double`（init） | 覆盖上/左边缘的标尺带厚度。 |
| `VerticalScrollBarThickness` / `HorizontalScrollBarThickness` | `double`（init） | 滚动条可见时的厚度，否则为零。 |
| `Available` | `SurfaceAvailableArea`（init） | 覆盖层可用的空闲角。 |
| `Create(double scrollOffsetX, double scrollOffsetY, double contentOffsetX, double contentOffsetY, double viewportWidth, double viewportHeight, double surfaceWidth, double surfaceHeight, double rulerBand, double verticalScrollBarThickness, double horizontalScrollBarThickness, double margin)` | `static SurfaceMetrics` | 由表面尺寸、标尺带和滚动条推导 `Available`。 |

`Create` 计算 `Available.Right = max(0, surfaceWidth − verticalScrollBarThickness)`、`Available.Top = max(0, rulerBand)`、`Available.Bottom = max(0, surfaceHeight − horizontalScrollBarThickness)`。

## SurfaceAvailableArea

**签名：** `readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Right` | `double`（init） | 可用右边缘。 |
| `Top` | `double`（init） | 可用上边缘，在水平标尺带之下。 |
| `Bottom` | `double`（init） | 可用下边缘，在水平滚动条之上。 |
| `Margin` | `double`（init） | 覆盖层与角落保持的间距。 |
| `IsUsable` | `bool` | `Right > 0 && Bottom > Top`。 |
| `GetRect(double desiredWidth, double desiredHeight, double minimumSize)` | `WorkflowBounds` | 在右上角放置一个矩形，钳制到可用区与最小尺寸；不可用时回退到原点。 |

`GetRect` 返回图几何 API 中的 `WorkflowBounds` 值类型。

## ISurfaceMetricsSource

**签名：** `interface ISurfaceMetricsSource`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ReadMetrics` | `SurfaceMetrics ReadMetrics()` | 读取当前度量。每次刷新都会调用，因此必须无分配且反映当前值。 |

## SurfaceMetricsPush

**签名：** `static class SurfaceMetricsPush`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `PushGrid` | `static void PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree)` | 写入四个偏移，并把 `RulerBand` 转发为树的虚拟化内缩。装饰器为 null 时抛 `ArgumentNullException`。 |
| `PushMinimap` | `static void PushMinimap(SurfaceMetrics metrics, IWorkflowMinimapOverlay minimap, ITreeComponent? tree)` | 写入偏移、视口尺寸、树与可用边缘。小地图为 null 时抛 `ArgumentNullException`。 |
| `PushViewport` | `static void PushViewport(SurfaceMetrics metrics, ITreeComponent tree)` | 按 `scroll − contentOffset` 写入 `tree.GetHelper().Viewport` 并持久化 `Layout.ViewportOffset`。树为 null 时抛 `ArgumentNullException`。 |

```csharp
var metrics = SurfaceMetrics.Create(
    scrollOffsetX: 120, scrollOffsetY: 80,
    contentOffsetX: 0, contentOffsetY: 0,
    viewportWidth: 800, viewportHeight: 600,
    surfaceWidth: 800, surfaceHeight: 600,
    rulerBand: 28, verticalScrollBarThickness: 12,
    horizontalScrollBarThickness: 12, margin: 12);

SurfaceMetricsPush.PushGrid(metrics, decorator, tree);
SurfaceMetricsPush.PushMinimap(metrics, minimap, tree);
SurfaceMetricsPush.PushViewport(metrics, tree);
```

**预期结果：** 调用 `PushViewport` 后，`tree.GetHelper().Viewport.Horizontal` 与 `tree.Layout.ViewportOffset.Horizontal` 都等于 `120`。

## SurfaceViewportFeed

**签名：** `sealed class SurfaceViewportFeed`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Current` | `SurfaceViewport?` | 最近一次发布的快照；首次发布前为 `null`。 |
| `Changed` | `event Action<SurfaceViewport>` | 每次发布时触发。 |
| `Publish(SurfaceViewport viewport)` | `void` | 保存快照并触发 `Changed`。 |

该推送通道让轻量覆盖层跟随视口，而不必强制节点/连线内容重绘。
