# API — 附加行为 · WorkflowSurfaceBehavior 与画布变换

## 类：`WorkflowSurfaceBehavior`

工作流表面宿主（承载编辑器 `ScrollViewer` + `Canvas` 双控件的控件）的附加行为。它解析命名的子控件、把滚动/内容偏移推送给网格装饰层与小地图、在「空白」表面按下时启动平移，并挂接缩放手势。

各适配器的宿主元素类型与属性注册方式不同：

| 适配器 | 宿主元素 | 声明形式 | 注册方式 |
|---|---|---|---|
| WPF / WinUI / Jalium | `UserControl` / `FrameworkElement`（Jalium） | `sealed class : DependencyObject` | `DependencyProperty.RegisterAttached` |
| Avalonia | `UserControl` | `sealed class : AvaloniaObject` | `AvaloniaProperty.RegisterAttached<WorkflowSurfaceBehavior, UserControl, T>` |
| MAUI | `ContentView` | `sealed class` | `BindableProperty.CreateAttached` |
| WinForms | `Control` | `sealed class` | 私有 `ConditionalWeakTable<Control, SurfaceState>` |
| Razor | 无（组件） | `partial class WorkflowSurfaceBehavior : ComponentBase, IAsyncDisposable` | 参数 |

### 附加属性表面（WPF / Avalonia / WinUI / MAUI / Jalium）

每个 XAML 风格适配器都暴露相同的附加属性与常见的 `Get*` / `Set*` 静态访问器（属性系统：WPF/WinUI/Jalium 为 `DependencyProperty`，Avalonia 为 `AvaloniaProperty`，MAUI 为 `BindableProperty`）：

| 属性 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `IsEnabled` | `bool` | `false` | 总开关：挂接 `Loaded` / `Unloaded` / `DataContextChanged` 与指针/滚动事件。 |
| `ScrollViewerName` | `string?` | `null` | 内部 `ScrollViewer` 的名称（如 `PART_ScrollViewer`）。 |
| `CanvasName` | `string?` | `null` | 内部 `Canvas` 的名称（如 `PART_Canvas`）。 |
| `GridDecoratorName` | `string?` | `null` | 实现 `IWorkflowGridDecorator` 的元素的名称。 |
| `PointerPressSourceName` | `string?` | `null` | 按下即开始平移的元素（表面边框）。 |
| `MinimapOverlayName` | `string?` | `null` | 实现 `IWorkflowMinimapOverlay` 的元素的名称。 |
| `ZoomEnabled` | `bool` | `false` | 启用框架缩放手势钩子（WPF：滚动查看器上的 `PreviewMouseWheel`）。 |

### 静态方法：`Refresh(host)`

重新解析命名控件、重放布局，并把可见区域推送给网格装饰层与小地图。在加载、滚动、`DataContextChanged` 以及平移/缩放更新后被调用。

| 适配器 | 签名 |
|---|---|
| WPF / Avalonia / WinUI | `public static void Refresh(UserControl host)` |
| MAUI | `public static void Refresh(ContentView host)` |
| WinForms | `public static void Refresh(Control host)` |
| Jalium | `public static void Refresh(FrameworkElement host)` |

**Jalium 额外成员 —— `ZoomBy`：**
`public static void ZoomBy(FrameworkElement host, IWorkflowTreeViewModel viewModel, double factor)` —— Jalium 把缩放作为显式调用（宿主驱动）而非滚轮钩子。

**WinForms 的表面另有** `SetWorkflowTree(Control element, IWorkflowTreeViewModel? value)`（对应 XAML 适配器免费获得的 `DataContext` 赋值）。

### WinForms 状态

WinForms 没有附加属性；`WorkflowSurfaceBehavior` 为每个 `Control` 通过 `ConditionalWeakTable` 维护私有 `SurfaceState`。状态里存同样的标志/名称外加 `WorkflowTree`，并安装 `IMessageFilter` 让 **Ctrl+滚轮缩放手势在任何可滚动子控件之前被拦截**：从滚轮消息的目标控件解析出表面宿主、应用 `tree.Layout.Scale` 与缩放中心滚动数学、标记消息已处理并吞掉它。*手势细节已按源码验证；未经自动化 Demo 驱动。*

### Razor 组件

`WorkflowSurfaceBehavior.razor` + 代码后置（`ComponentBase`）以参数替代附加属性：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `Tree` | `IWorkflowTreeViewModel?` | `null` | 要承载的树。 |
| `IsEnabled` | `bool` | `false` | 启用行为接线。 |
| `ZoomEnabled` | `bool` | `false` | 启用滚轮缩放。 |
| `ScrollViewerId` | `string` | `"veloxdev-wf-scroll"` | 滚动元素的 `id`。 |
| `CanvasId` | `string` | `"veloxdev-wf-canvas"` | 画布元素的 `id`。 |
| `GridDecorator` | `RenderFragment<SurfaceViewport>?` | `null` | 网格装饰层片段。 |
| `Minimap` | `RenderFragment<SurfaceViewport>?` | `null` | 小地图片段。 |
| `ChildContent` | `RenderFragment<SurfaceCanvas>?` | `null` | 节点/槽内容。 |
| `Background`、`GridColor`、`MajorGridColor`、`AxisColor` | `string` | CSS 颜色 | 表面视觉。 |
| `GridSpacing` | `double` | `40` | 次要网格间距。 |
| `MajorLineEvery` | `int` | `5` | 主网格线节奏。 |
| `RulerThickness` | `double` | `28` | 标尺带尺寸。 |

公共方法 `OnWheelZoom(int wheelDelta, double scrollX, double scrollY, double viewportW, double viewportH, double reachW, double reachH)` 与 `OnSurfaceScroll(...)` 是 JS 回调；`DisposeAsync` 解除挂接。组件渲染画布并把节点/连接几何经由 Razor 互操作通道交给浏览器。

## 类：`WorkflowCanvasTransformBehavior`

持有节点/连接视图使用的画布渲染变换。在 XAML 适配器中，节点与连接视图把 `RenderTransform` 绑定到宿主的附加 `(WorkflowCanvasTransformBehavior.Transform)`；表面行为在这里写入平移偏移，而不是用反射。

| 适配器 | 形态 | 公共 API |
|---|---|---|
| WPF / WinUI / Jalium | `public static class` | 附加 `Transform`（WPF/WinUI：`System.Windows.Media.Transform`；Jalium：`Jalium.UI.Media.Transform`）；`GetTransform(UIElement)`、`SetTransform(UIElement, Transform?)`、internal `Apply(UIElement, Transform)` |
| Avalonia | `public sealed class : AvaloniaObject` | `AttachedProperty<ITransform?>` `Transform`；`GetTransform(AvaloniaObject)`、`SetTransform(AvaloniaObject, ITransform?)`、internal `Apply(Control, ITransform)` |
| WinForms | `public static class` | 保存一个 `Offset`（无渲染变换）；`GetTransform(Control)`、`SetTransform(Control, Offset?)`、internal `Apply(Control, Offset)` |
| Razor | `public static class` | `GetOffset(IWorkflowTreeViewModel tree)` → `CanvasLayout.ActualOffset`；`ToCss(Offset)` → `translate(px, px)`；`GetTransformStyle(tree)` → CSS 变换字符串 |
| MAUI | 不提供 | MAUI 改由 `WorkflowLinkOverlay` 渲染连接 |

**Jalium 说明：** Jalium 上由 `ViewManager` 把变换镜像到活动节点/连接视图的 `RenderTransform`；宿主自身绝不接收它。
