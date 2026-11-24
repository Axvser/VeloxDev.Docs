# 小地图覆盖层

`WorkflowMinimapOverlay` 是 WinUI `Canvas`，实现 `IWorkflowMinimapOverlay`。它绘制缩略图与视口框，并通过表面的 `ScrollViewerName` 导航。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（覆盖层）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.WinUI`。

## WorkflowMinimapOverlay

**签名：** `class WorkflowMinimapOverlay : Canvas, IWorkflowMinimapOverlay`

### 数据与布局属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 画布内容偏移。 |
| `WorkflowTree` | `ITreeComponent?` | `null` | 要渲染的树。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | 滚动空间中的视口尺寸。 |
| `IsMinimapVisible` | `bool` | `true` | 小地图是否绘制。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | 缩略图尺寸。 |
| `MinimapMargin` | `double` | `12` | 与可用角的间距。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | 可用角边缘。 |
| `RulerThickness` | `double` | `28` | 覆盖层避让的标尺带。 |
| `LinkStrokeThickness` | `double` | `2` | 缩略图连线线宽。 |
| `ScrollViewerName` | `string?` | `null` | 要导航的滚动容器。 |
| `RulerBand` | `double` | 只读 `0` | 不绘制标尺带。 |

### 外观属性

画刷属性与 WPF 一致：`MinimapBackground`、`MinimapBorderBrush`、`NodeBrush`、`LinkBrush`、`ViewportStroke`、`ViewportFill`（`Brush?`），以及 `ViewportStrokeThickness`、`MinimapCornerRadius`、`MinimapBorderThickness`、`NodeCornerRadius`、`ContentPadding`、`MinimapMinSize`（`double`）。

导航遵循始终居中规则：在缩略图任意位置按下会把视口重新居中。

**预期结果：** 小地图跟随滚动；点击经与滚轮相同的唯一写入口重新居中表面。

## MinimapPipeline

**签名：** `sealed class MinimapPipeline : MinimapPipelineCore<WorkflowMinimapOverlay, IMinimapRenderer<WorkflowMinimapOverlay>, IMinimapViewportHost, IMinimapInputHost>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<WorkflowMinimapOverlay> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | 构造函数 | 组合三个层。 |

## MinimapRenderer

**签名：** `sealed class MinimapRenderer : IMinimapRenderer<WorkflowMinimapOverlay>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | 构造函数 | null 时抛 `ArgumentNullException`。 |
| `Render(WorkflowMinimapOverlay surface, MinimapDrawContext context)` | `void` | 委托给宿主的受保护 `DrawMinimapSurface`。 |

## MinimapViewportHost

**签名：** `sealed class MinimapViewportHost : IMinimapViewportHost`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `MinimapViewportHost(WorkflowMinimapOverlay owner)` | 构造函数 | 读取推送的偏移并通过表面应用滚动。 |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | 来自覆盖层的当前状态。 |
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
