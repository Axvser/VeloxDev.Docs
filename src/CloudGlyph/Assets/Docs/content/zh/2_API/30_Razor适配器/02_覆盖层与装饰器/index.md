# 覆盖层与装饰器

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

两个组件都消费表面提供的 `SurfaceViewport`，并实现与 XAML 适配器相同的 Core 接口，宿主因此可以把标尺/小地图设置跨平台沿用。

## 类：WorkflowGridDecorator

`public partial class WorkflowGridDecorator : ComponentBase, IWorkflowGridDecorator, IDisposable`

镜像表面滚动/内容偏移的标尺条。带本身由表面的 JS 与滚动同帧移动；只有刻度窗口可能需要一次服务端渲染。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Viewport` | `SurfaceViewport?` | `null` | 表面推入的视口上下文。 |
| `ViewportFeed` | `SurfaceViewportFeed?` | `null` | `[CascadingParameter]`；每次视口变化只更新轻量刻度层。 |
| `RulerThickness` | `double` | `28` | 标尺带厚度（像素）。 |
| `Spacing` | `double` | `40` | 刻度间距（像素）。 |
| `RulerBackground` | `string` | `"rgba(37,37,38,0.78)"` | 带填充。 |
| `TickColor` | `string` | `"#555555"` | 刻度颜色。 |
| `LabelColor` | `string` | `"#888888"` | 数字标签颜色。 |
| `MajorLineEvery` | `int` | `5` | 每个主刻度的次格数。 |
| `DividerColor` | `string` | `"#3A3D40"` | 标尺分隔线颜色。 |
| `AxisColor` | `string?` | `null` | 世界零刻度颜色；默认取 `TickColor`。 |

### 接口属性

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 表面滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 有效世界原点。 |
| `RulerBand` | `double` | 返回 `RulerThickness`。 |

`public void Dispose()` 退订 `ViewportFeed`。

### 备注

- 刻度集合覆盖可见范围周围的窗口，而不是精确可见范围；逐帧位移由 JS 平移完成。
- 没有单位的 CSS 长度无效；内部值都带 `px`，小数点固定为 `.`。

## 类：WorkflowMinimapOverlay

`public partial class WorkflowMinimapOverlay : ComponentBase, IWorkflowMinimapOverlay, IAsyncDisposable`

整面、可穿透点击的缩略图层。内层小地图盒按 JS 测得的可用区放置在内容视口右上角。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Viewport` | `SurfaceViewport?` | `null` | 表面推入的视口上下文。 |
| `Width` | `double` | `180` | 小地图宽度（像素）。 |
| `Height` | `double` | `120` | 小地图高度（像素）。 |
| `Background` | `string` | `"#331E1E1E"` | 小地图背景。 |
| `BorderColor` | `string` | `"#DC94A3B8"` | 小地图边框。 |
| `NodeFill` | `string` | `"#DC38BDF8"` | 节点填充。 |
| `NodeRadius` | `double` | `2` | 节点圆角。 |
| `ViewportFill` | `string` | `"rgba(255,255,255,0.15)"` | 视口指示块填充。 |
| `ViewportStroke` | `string` | `"#F0FFFFFF"` | 视口指示块描边。 |
| `ViewportStrokeWidth` | `double` | `1.5` | 视口指示块描边宽度。 |
| `Padding` | `double` | `6` | 映射内容周围的内边距。 |
| `ScrollViewerId` | `string?` | `null` | 要测量与导航的表面滚动容器。 |
| `DrawMinimap` | `RenderFragment<MinimapDrawContext>?` | `null` | 默认节点与视口块之后的追加内容。 |

### 接口属性

| 成员 | 类型 |
| --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` |
| `ContentOffsetX` / `ContentOffsetY` | `double` |
| `RulerBand` | `double`（恒为 `0`） |
| `ViewportWidth` / `ViewportHeight` | `double` |
| `WorkflowTree` | `ITreeComponent?` |
| `IsMinimapVisible` | `bool` |
| `MinimapMargin` | `double`（默认 `12`） |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `OnMinimapAreaMeasured(double availableRight, double availableTop, double availableBottom, double overlayWidth)` | `void` | `[JSInvokable]`；接收 JS 测得的空闲角。 |
| `OnMinimapScrollRange(double maximumX, double maximumY)` | `void` | `[JSInvokable]`；缓存 DOM 滚动上限。 |
| `DisposeAsync()` | `ValueTask` | 释放流水线、节流与 JS 句柄。 |

### 备注

- `DrawMinimap` 是渲染片段，不是虚方法：Blazor 组件不能覆盖另一个组件的渲染树。
- 视口块由 JS 在滚动时直接移动，滚动因此只花一次小互操作，而不是整棵 .NET 重渲染。
- 拖拽导航留在 JS：本适配器把越界量放在模型之外，套用 Core 的拖拽数学会把内容平移两次。
