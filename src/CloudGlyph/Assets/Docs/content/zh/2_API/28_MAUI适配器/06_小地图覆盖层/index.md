# 小地图覆盖层

`WorkflowMinimapOverlay` 是 MAUI `Grid`，实现 `IWorkflowMinimapOverlay` 与 `IDrawable`。它通过 `ICanvas` 绘制缩略图，并通过表面的 `ScrollViewerName` 导航。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（覆盖层）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.MAUI`。

## WorkflowMinimapOverlay

**签名：** `class WorkflowMinimapOverlay : Grid, IDrawable, IWorkflowMinimapOverlay`

### 数据与布局属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 画布内容偏移。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | 滚动空间中的视口尺寸。 |
| `IsMinimapVisible` | `bool` | `true` | 小地图是否绘制。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | 缩略图尺寸。 |
| `MinimapMargin` | `double` | `12` | 与可用角的间距。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | 可用角边缘。 |
| `RulerThickness` | `double` | `28` | 覆盖层避让的标尺带。 |
| `LinkStrokeThickness` | `double` | `2` | 缩略图连线线宽。 |
| `ScrollViewerName` | `string?` | `null` | 要导航的 `ScrollView`。 |
| `RulerBand` | `double` | 只读 `0` | 不绘制标尺带。 |

### 外观属性

此适配器使用 `Color` 而非画刷：

| 属性 | 默认值 |
| --- | --- |
| `MinimapBackgroundColor` | `Color.FromRgba(30, 30, 30, 51)` |
| `MinimapBorderColor` | `Color.FromRgba(148, 163, 184, 220)` |
| `NodeFillColor` | `Color.FromRgba(56, 189, 248, 220)` |
| `LinkStrokeColor` | `Color.FromRgba(180, 200, 220, 180)` |
| `ViewportStrokeColor` | `Color.FromRgba(255, 255, 255, 240)` |
| `ViewportFillColor` | `Color.FromRgba(255, 255, 255, 40)` |
| `ViewportStrokeThickness` | `1.5` |
| `MinimapCornerRadius` | `4` |
| `MinimapBorderThickness` | `1` |
| `NodeCornerRadius` | `1` |
| `ContentPadding` | `2` |
| `MinimapMinSize` | `20` |

导航遵循始终居中规则：在缩略图任意位置按下会把视口重新居中。

**预期结果：** 小地图跟随滚动，点击通过解析出的 `ScrollView` 重新居中表面。

## MinimapPipeline

**签名：** `sealed class MinimapPipeline : MinimapPipelineCore<ICanvas, IMinimapRenderer<ICanvas>, IMinimapViewportHost, IMinimapInputHost>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<ICanvas> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | 构造函数 | 组合各层。 |

## MinimapRenderer

**签名：** `sealed class MinimapRenderer : IMinimapRenderer<ICanvas>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | 构造函数 | null 时抛 `ArgumentNullException`。 |
| `Render(ICanvas surface, MinimapDrawContext context)` | `void` | 委托给宿主的受保护 `DrawMinimapSurface`。 |

## MinimapViewportHost

**签名：** `sealed class MinimapViewportHost : IMinimapViewportHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapViewportHost(WorkflowMinimapOverlay owner)` | 构造函数 | 读取推送的偏移并滚动解析出的 `ScrollView`。 |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | 当前状态，已清洗为有限值。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 视口尺寸。 |
| `ScrollableWidth` / `ScrollableHeight` | `double` | 可滚动范围。 |
| `ApplyScroll(double x, double y)` | `void` | 应用滚动位置。 |

## MinimapInputHost

**签名：** `sealed class MinimapInputHost : IMinimapInputHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Capture()` | `bool` | 为拖拽捕获。 |
| `Release()` | `void` | 释放捕获。 |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | 属性 | 指针状态与钳制矩形。 |
