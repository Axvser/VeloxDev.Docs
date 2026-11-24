# 小地图覆盖层

`WorkflowMinimapOverlay` 是 Avalonia `Control`，实现 `IWorkflowMinimapOverlay` 与 `ICustomHitTest`。它绘制缩略图与视口框，并通过表面的 `ScrollViewerName` 把按下变成导航。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（覆盖层）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.Avalonia`。

## WorkflowMinimapOverlay

**签名：** `class WorkflowMinimapOverlay : Control, IWorkflowMinimapOverlay, ICustomHitTest`

### 数据与布局属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 画布内容偏移。 |
| `WorkflowTree` | `ITreeComponent?` | `null` | 要渲染的树。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `0` | 滚动空间中的视口尺寸。 |
| `IsMinimapVisible` | `bool` | `true` | 小地图是否绘制。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | 缩略图尺寸。 |
| `MinimapMargin` | `double` | `12` | 与可用角的间距。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | 可用角边缘。 |
| `RulerThickness` | `double` | `28` | 覆盖层避让的标尺带。 |
| `LinkStrokeThickness` | `double` | `2` | 缩略图连线线宽。 |
| `ScrollViewerName` | `string` | `""` | 要导航的滚动容器；此适配器上非空。 |
| `RulerBand` | `double` | 只读 `0` | 不绘制标尺带。 |

### 外观属性

| 属性 | 类型 | 默认值 |
| --- | --- | --- |
| `MinimapBackground` | `IBrush?` | 半透明深色（`#331E1E1E`） |
| `MinimapBorderBrush` | `IBrush?` | `#DC94A3B8` |
| `NodeBrush` | `IBrush?` | `#DC38BDF8` |
| `LinkBrush` | `IBrush?` | `#B4B4C8DC` |
| `ViewportStroke` | `IBrush?` | `#F0FFFFFF` |
| `ViewportFill` | `IBrush?` | `#28FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `MinimapCornerRadius` | `double` | `4` |
| `MinimapBorderThickness` | `double` | `1` |
| `NodeCornerRadius` | `double` | `1` |
| `ContentPadding` | `double` | `2` |
| `MinimapMinSize` | `double` | `20` |

导航遵循始终居中规则：在缩略图任意位置按下会把该点重新居中到视口。

```xml
<behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                  HorizontalAlignment="Stretch"
                                  VerticalAlignment="Stretch"
                                  ScrollViewerName="PART_ScrollViewer" />
```

**预期结果：** 小地图跟随滚动，点击会重新居中表面。

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
| `MinimapViewportHost(ScrollViewer scrollViewer)` | 构造函数 | 直接驱动 `ScrollViewer`；覆盖层内部使用覆盖层支撑的形式。 |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | 当前状态。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 视口尺寸。 |
| `ScrollableWidth` / `ScrollableHeight` | `double` | 可滚动范围。 |
| `ApplyScroll(double x, double y)` | `void` | 应用滚动位置。 |

## MinimapInputHost

**签名：** `sealed class MinimapInputHost : IMinimapInputHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapInputHost()` | 构造函数 | 创建指针状态宿主。 |
| `Capture()` | `bool` | 为拖拽捕获。 |
| `Release()` | `void` | 释放捕获。 |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | 属性 | 指针状态与钳制矩形。 |
