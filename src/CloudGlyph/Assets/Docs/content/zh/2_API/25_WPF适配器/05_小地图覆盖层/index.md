# 小地图覆盖层

`WorkflowMinimapOverlay` 是 `FrameworkElement`，实现 `IWorkflowMinimapOverlay`：绘制节点/连线缩略图、视口框，并把按下变成滚动。它与表面共享 `ScrollViewerName` 解析，因此元素必须命名与表面相同的滚动容器。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（覆盖层）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.WPF`。

## WorkflowMinimapOverlay

**签名：** `class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay`

### 数据与布局属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面推动的滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 画布内容偏移。 |
| `WorkflowTree` | `ITreeComponent?` | `null` | 要渲染的树。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | 滚动空间中的视口尺寸。 |
| `IsMinimapVisible` | `bool` | `true` | 小地图是否绘制。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | 缩略图尺寸。 |
| `MinimapMargin` | `double` | `12` | 与可用角的间距。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | 表面推动的可用角边缘。 |
| `RulerThickness` | `double` | `28` | 覆盖层避让的标尺带。 |
| `LinkStrokeThickness` | `double` | `2` | 缩略图连线线宽。 |
| `ScrollViewerName` | `string?` | `null` | 要导航的滚动容器。 |
| `RulerBand` | `double` | 只读 `0` | 覆盖层不绘制标尺带。 |

### 外观属性

| 属性 | 类型 | 默认值 |
| --- | --- | --- |
| `MinimapBackground` | `Brush?` | 半透明深色（`#331E1E1E`） |
| `MinimapBorderBrush` | `Brush?` | `#DC94A3B8` |
| `NodeBrush` | `Brush?` | `#DC38BDF8` |
| `LinkBrush` | `Brush?` | `#B4B4C8DC` |
| `ViewportStroke` | `Brush?` | `#F0FFFFFF` |
| `ViewportFill` | `Brush?` | `#28FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `MinimapCornerRadius` | `double` | `4` |
| `MinimapBorderThickness` | `double` | `1` |
| `NodeCornerRadius` | `double` | `1` |
| `ContentPadding` | `double` | `2` |
| `MinimapMinSize` | `double` | `20` |

导航遵循始终居中规则：在缩略图任意位置按下，会把该世界点放到视口中心。覆盖层不自行决定滚动；`MinimapViewportHost` 把拖拽解析成偏移。

```xml
<behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                  HorizontalAlignment="Stretch"
                                  VerticalAlignment="Stretch"
                                  ScrollViewerName="PART_ScrollViewer" />
```

**预期结果：** 缩略图显示图，视口框随滚动移动，点击会重新居中表面。

## MinimapPipeline

**签名：** `sealed class MinimapPipeline : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>, IMinimapViewportHost, IMinimapInputHost>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<DrawingContext> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | 构造函数 | 组合三个层。 |

## MinimapRenderer

**签名：** `sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | 构造函数 | null 时抛 `ArgumentNullException`。 |
| `Render(DrawingContext surface, MinimapDrawContext context)` | `void` | 委托给宿主的受保护 `DrawMinimapSurface`。 |

## MinimapViewportHost

**签名：** `sealed class MinimapViewportHost : IMinimapViewportHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapViewportHost(ScrollViewer scrollViewer)` | 构造函数 | 直接驱动 `ScrollViewer`。 |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | 当前状态；由覆盖层构造时覆盖层推动的值优先。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 视口尺寸。 |
| `ScrollableWidth` / `ScrollableHeight` | `double` | 可滚动范围。 |
| `ApplyScroll(double x, double y)` | `void` | 应用滚动位置。 |

## MinimapInputHost

**签名：** `sealed class MinimapInputHost : IMinimapInputHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapInputHost()` | 构造函数 | 创建指针状态宿主。 |
| `Capture()` | `bool` | 为拖拽捕获指针。 |
| `Release()` | `void` | 释放指针。 |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | 属性 | 指针状态与拖拽钳制矩形。 |
