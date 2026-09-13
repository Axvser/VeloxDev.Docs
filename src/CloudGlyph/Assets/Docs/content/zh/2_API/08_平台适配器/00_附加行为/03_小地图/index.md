# API — 附加行为 · 小地图覆盖层

`WorkflowMinimapOverlay` 渲染所有节点/连接的缩略图外加一个可拖拽的视口指示框，让用户看到并导航整个工作流。它实现 Core 的数据交换契约 `IWorkflowMinimapOverlay`（因而也实现 `IWorkflowGridDecorator`）。

## 类：`WorkflowMinimapOverlay`

| 适配器 | 声明形式 | 绘制模型 |
|---|---|---|
| WPF | `public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay` | OnRender 几何 |
| Avalonia | `public class WorkflowMinimapOverlay : Control, IWorkflowMinimapOverlay` | 控件渲染（StyledProperty） |
| WinUI | `public class WorkflowMinimapOverlay : Canvas, IWorkflowMinimapOverlay` | XAML `Rectangle` / `Line` 形状 |
| MAUI | `public class WorkflowMinimapOverlay : GraphicsView, IDrawable, IWorkflowMinimapOverlay` | `IDrawable.Draw(ICanvas, RectF)` |
| WinForms | `public static class WorkflowMinimapOverlay` | 绘制已注册控件的表面 |
| Jalium | `public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay` | OnRender 几何 |
| Razor | `partial class WorkflowMinimapOverlay : ComponentBase, IWorkflowMinimapOverlay, IAsyncDisposable` | 经 JS 互操作的 SVG/DOM |

### 共享属性表面（WPF / Avalonia / WinUI / MAUI / Jalium）

除接口成员外，覆盖层还暴露样式/几何属性。下面为 WPF 示例（其它平台同名；`Brush` ↔ `IBrush`/`Color` 依平台而别）：

| 属性 | 类型 | 默认（WPF） |
|---|---|---|
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` |
| `RulerThickness` | `double` | `28` |
| `LinkStrokeThickness` | `double` | `2` |
| `MinimapBackground` / `MinimapBorderBrush` | 画刷 | 深蓝灰 / 边框 |
| `NodeBrush` / `LinkBrush` | 画刷 | 天蓝 / 浅灰 |
| `ViewportStroke` / `ViewportFill` / `ViewportStrokeThickness` | 画刷 / 画刷 / `double` | 白色描边、半透明填充 |
| `MinimapCornerRadius` / `MinimapBorderThickness` / `NodeCornerRadius` | `double` | `4` / `1` / `1` |
| `ContentPadding` / `MinimapMinSize` | `double` | `2` / `20` |
| `ScrollViewerName` | `string?` | `null`（加载时解析，用于拖拽导航） |
| `RulerBand`（接口上的只读） | `double` | 小地图自身为 `0` |

MAUI 用颜色类型的可绑定属性而非画刷（`MinimapBackgroundColor`、`MinimapBorderColor`、`NodeFillColor`、`LinkStrokeColor`、`ViewportStrokeColor`、`ViewportFillColor`、……），Avalonia 用 `IBrush` `StyledProperty` 并多一个 `MinimapMargin`。*各平台默认值已按源码验证；跨适配器的视觉对等属 `*推断所得*`。*

### 行为（已验证，WPF）

- 订阅树的节点/连接集合作脏跟踪，并重测世界边界。
- **视口拖拽：** 在视口矩形内按下时保持其位置并对齐到光标；在别处按下时把视口块中心移到光标处，并夹在小地图内。
- **导航到世界：** 把小地图坐标映射回世界坐标并滚动 `ScrollViewer`，在边缘增长 `Layout.NegativeOffset` / `PositiveOffset`。
- 表面行为在每次渲染前推送 `ScrollOffset*`、`ContentOffset*`、`ViewportWidth/Height`、`WorkflowTree` 与 `IsMinimapVisible`。

## 接口：`IWorkflowGridDecorator`

网格装饰层的数据交换契约；表面行为在每次渲染前把滚动偏移与画布内容偏移推给它。**定义于 Core**（`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowGridDecorator.cs`，命名空间 `VeloxDev.WorkflowSystem`），七个适配器共用一份定义。

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double RulerBand { get; }
}
```

`RulerBand` 是装饰层绘制在画布内容 TOP/LEFT 边缘的浮动标尺/刻度带厚度；适配器表面读取它并转发给 `WorkflowSpatialEx.SetVirtualizeInset`，使空间虚拟化不会剔除仍位于标尺带下的节点。

## 接口：`IWorkflowMinimapOverlay`

派生自 `IWorkflowGridDecorator`（小地图同样需要滚动/内容偏移），再加视口尺寸与要渲染的树。**定义于 Core**（`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowMinimapOverlay.cs`，命名空间 `VeloxDev.WorkflowSystem`）。

```csharp
public interface IWorkflowMinimapOverlay : IWorkflowGridDecorator
{
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    IWorkflowTreeViewModel? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
}
```

## WinForms 静态覆盖层

WinForms 的 `WorkflowMinimapOverlay` 是静态附加风格持有类：`SetIsEnabled(Control, bool)` / `SetWorkflowTree(Control, IWorkflowTreeViewModel?)` 及对应 getter。行为在控件上注册绘制处理；实际缩略图画进控件的 `Paint` 表面。*细节由源码推断所得 —— 没有自动化 Demo 绘制它。*

## Razor 组件

`WorkflowMinimapOverlay.razor` + 代码后置实现 `IWorkflowMinimapOverlay`，参数为 `Width`（180）、`Height`（120）、`Background`、`BorderColor`、`NodeFill`、`NodeRadius`、`ViewportFill`、`ViewportStroke`、`ViewportStrokeWidth`、`Padding`、`ScrollViewerId`，外加六个接口偏移/视口成员。拖拽导航经滚动 `id` 解析并更新 `ScrollOffset*`。
