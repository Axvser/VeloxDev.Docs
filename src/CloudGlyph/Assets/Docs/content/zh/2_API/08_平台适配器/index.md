# 平台适配器 — API 参考

六个 GUI 适配器（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`）共享 `VeloxDev.WorkflowSystem.AttachedBehaviors` 命名空间下的同一套行为表面，外加 `VeloxDev.TransitionSystem` / `VeloxDev.DynamicTheme` 命名空间中的各平台过渡/主题接线。验证过的名称来自 WPF 适配器源码与 WPF/Avalonia/Blazor 演示；未经演示覆盖的内容标注为 `*推断所得*`。

## 命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`

每个适配器都带这些类型。WPF/Avalonia/Razor 已由演示覆盖；WinUI/MAUI/WinForms 暴露同名类型（源码已验证），但其各平台行为细节为 `*推断所得*`。

### 类：`WorkflowSurfaceBehavior`

工作流画布宿主（一个 `UserControl`）的附加行为。负责平移、指针跟踪、可见区域更新，以及网格/小地图的数据推送。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 总开关。为 `true` 时行为会挂接宿主的 `Loaded` / `Unloaded` / `DataContextChanged` / 鼠标事件。 |
| `ScrollViewerName` | 附加 `string?` | 内部 `ScrollViewer` 的名称（例如 `PART_ScrollViewer`）。 |
| `CanvasName` | 附加 `string?` | 内部 `Canvas` 的名称（例如 `PART_Canvas`）。 |
| `GridDecoratorName` | 附加 `string?` | 实现 `IWorkflowGridDecorator` 的元素的名称。 |
| `PointerPressSourceName` | 附加 `string?` | 按下即开始平移的元素（画布边框）。 |
| `MinimapOverlayName` | 附加 `string?` | 实现 `IWorkflowMinimapOverlay` 的元素的名称。 |
| `Refresh` | `static void Refresh(UserControl host)` | 重新解析命名控件、重放布局、更新可见区域。在加载、滚动、`DataContextChanged` 时被调用。 |

**行为（已验证，WPF）：** 只在「空白」画布上点击（不在节点/槽视觉元素或滚动条上方）才启动平移；把画布坐标喂给 `SetPointerCommand`；由滚动偏移更新 `GetHelper().Viewport`；并持久化 `Layout.ViewportOffset` 以便序列化往返。

### 静态类：`WorkflowCanvasTransformBehavior`

持有节点/连接视图使用的画布渲染变换。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Transform` | 附加 `Transform?` | 节点/连接视图把 `RenderTransform` 绑定到宿主的 `(behaviors:WorkflowCanvasTransformBehavior.Transform)`。 |
| `Apply` | `internal static void Apply(UIElement, Transform)` | `WorkflowSurfaceBehavior` 在这里写入平移偏移，而不是用反射。 |

### 类：`ViewPool`

对 `Panel` 的附加对象池支持。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `ItemsSource` | 附加 `INotifyCollectionChanged?` | 例如 `behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"`。 |
| `TemplateSelector` | 附加 `DataTemplateSelector?` | 按视图模型类型选择项模板。 |

### 类：`ViewManager`

按面板创建、由 `ViewPool` 持有的密封管理器。按 `Type` 用 `Queue<FrameworkElement>` 池化视图，维护活动视图与待处理批次，并按每 dispatcher `Background` 滴答 **3** 个一批渲染。被移除的项折叠为 `Visibility.Collapsed`、解绑并归还池。模板查找顺序：`ViewPool.TemplateSelector` → 资源树 → `Application.Current.Resources`。*WPF 中已验证；Avalonia/MAUI/WinUI/WinForms 的 `ViewManager` 遵循相同模式（批量大小是否一致为 `*推断所得*`）。*

### 类：`WorkflowNodeDragBehavior`

让节点可拖拽的附加行为。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 启用捕获与移动处理。 |
| `CoordinateHostName` | 附加 `string?` | 计算增量时使用的坐标空间元素名。 |
| `CoordinateHostType` | 附加 `Type?` | 回退宿主类型；默认为 `Canvas`。 |

按下时捕获鼠标；移动时执行 `node.MoveCommand.Execute(new Offset(current - last))`；松开/丢失捕获时停止。

### 类：`WorkflowSlotConnectionBehavior`

通过按下/松开连接槽的附加行为。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 启用按下/松开处理。 |

按下时执行 `slot.SendConnectionCommand.Execute(null)`；松开时执行 `slot.ReceiveConnectionCommand.Execute(null)`。

### 类：`WorkflowSlotLayoutBehavior`

让槽锚点与节点布局保持同步。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 启用布局同步。 |
| `SlotNames` | 附加 `string?` | 逗号分隔的单个槽控件名（例如 `PART_InputSlot`）。 |
| `SlotEnumeratorNames` | 附加 `string?` | 逗号分隔的、枚举槽的 `ItemsControl` 名（例如 `PART_OutputSlots`）。 |
| `CoordinateHostName` | 附加 `string?` | 计算锚点时使用的坐标空间。 |
| `CoordinateHostType` | 附加 `Type?` | 回退宿主类型；默认为 `Canvas`。 |

它监视节点的 `Anchor`/`Size`/槽属性，并用 `TranslatePoint` 找到槽中心后重新计算每个槽的 `Anchor`（计入 `Layout.ActualOffset`）。

### 类：`WorkflowMinimapOverlay`

`FrameworkElement : IWorkflowMinimapOverlay`（WPF/Avalonia/WinUI/MAUI）。渲染所有节点/连接的缩略图外加可拖拽的视口指示框。

| 属性 | 类型 | 说明 |
|---|---|---|
| `ScrollOffsetX/Y`、`ContentOffsetX/Y` | `double` | 由画布行为推送。 |
| `WorkflowTree` | `IWorkflowTreeViewModel?` | 订阅节点/连接集合以做脏跟踪。 |
| `ViewportWidth/Height` | `double` | 可见视口尺寸。 |
| `IsMinimapVisible` | `bool` | 切换渲染。 |
| `MinimapWidth/Height` | `double` | 默认 200 × 140。 |
| `RulerThickness`、`LinkStrokeThickness` | `double` | 视觉尺寸。 |
| `MinimapBackground/BorderBrush`、`NodeBrush`、`LinkBrush`、`ViewportStroke/Fill`、`ViewportStrokeThickness` | `Brush` / `double` | 视觉。 |
| `ScrollViewerName` | `string?` | 加载时解析，用于拖拽导航。 |

拖拽逻辑（已验证，WPF）：在视口矩形内部按下时保持其位置并对齐到光标；在别处按下时把视口块中心移到光标处，并夹在小地图内。`NavigateToWorld` 把小地图坐标映射回世界坐标并滚动 `ScrollViewer`，在边缘增长 `Layout.NegativeOffset`/`PositiveOffset`。

### 接口：`IWorkflowGridDecorator`

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
}
```

由网格装饰层视图实现（例如 `wpf-v-decorator` 生成的 `GridDecorator`），让 `WorkflowSurfaceBehavior` 无需反射即可推送偏移。

### 接口：`IWorkflowMinimapOverlay`

```csharp
public interface IWorkflowMinimapOverlay
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    IWorkflowTreeViewModel? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
}
```

## 命名空间：`VeloxDev.TransitionSystem`（各平台接线）

每个适配器都提供 `Interpolator`、`TransitionEffect`、`TransitionEffects`、`UIThreadInspector`、`State` 与 `Interpolators/*` 集合。基础引擎见 [过渡系统](1_TransitionSystem) API 页。

### 类：`Interpolator`

`Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>`。静态构造函数注册平台类型：

| 适配器 | 注册类型（静态构造） |
|---|---|
| WPF | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D` |
| Avalonia | `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength` |
| WinUI | `Brush`、`Color`、`CornerRadius`、`GridLength`、`Point`、`Projection`、`Rect`、`Size`、`Thickness`、`Transform` |
| MAUI | `Brush`、`Color`、`CornerRadius`、`Point`、`PointF`、`Rect`、`RectF`、`Shadow`、`Size`、`SizeF`、`Thickness`、`Transform` |
| WinForms | `Padding` |
| Razor | `string` → `StringInterpolator` |

`Interpolators/*` 目录为每种类型一个类（例如 WPF 的 `BrushInterpolator`、`ThicknessInterpolator`、`TransformInterpolator`、`CornerRadiusInterpolator`、`PointInterpolator`、`ColorInterpolator`、`DropShadowEffectInterpolator`、`Point3DInterpolator`、`Vector3DInterpolator`、`SizeInterpolator`、`RectInterpolator`、`VectorInterpolator`）。非 WPF 平台的插值器类经源码验证存在；确切的注册清单按类型名加旧 wiki（Avalonia）为 `*推断所得*`。

### 类：`TransitionEffect`

`TransitionEffect : TransitionEffectCore<TPriorityCore>`。默认优先级：

| 适配器 | 优先级类型 | 默认优先级 |
|---|---|---|
| WPF | `DispatcherPriority` | `DispatcherPriority.Render` |
| Avalonia | `DispatcherPriority` | `DispatcherPriority.Render` |
| WinUI | `DispatcherQueuePriority` | `DispatcherQueuePriority.High` |
| MAUI / WinForms / Razor | 无 | n/a（无优先级泛型参数） |

### 类：`TransitionEffects`

静态预设：`Empty`（`Duration = TimeSpan.Zero`）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。**注意：** WinUI 适配器中 `TransitionEffects` 是**非静态**类（成员仍是 `static`）；其余各处为 `public static class TransitionEffects`。

### 类：`UIThreadInspector`

`UIThreadInspector : UIThreadInspectorCore[<TPriorityCore>]`。把逐帧写入编组到 UI 线程：

| 适配器 | 线程来源 | 说明 |
|---|---|---|
| WPF | `Application.Current?.Dispatcher` | 优先使用目标 `DispatcherObject` 自身的 dispatcher；回退到 `Application.Current`。 |
| Avalonia | `Dispatcher.UIThread` | 使用 `CheckAccess` / `InvokeAsync`。 |
| WinUI | `DispatcherQueue` | 惰性捕获 `DispatcherQueue.GetForCurrentThread()`；显式 `static CaptureUIThread()`。`DependencyObject` 目标使用自己的队列。*旧 wiki 提到需要 `SetWindow(Window)` — 当前源码中不存在。* |
| MAUI | `Application.Current?.Dispatcher` | `IsUIThread()` 即 `IsDispatchRequired == false`。 |
| WinForms | `SynchronizationContext` + `static CaptureUIThread()` | 目标 `Control` 在句柄存在时通过 `Control.Invoke` / `BeginInvoke` 编组。 |
| Razor | `SynchronizationContext` + `static CaptureUIThread()` | 另有 `static NotifyShutdown()`。 |

### 类：`State`

`public class State : StateCore { }` — 适配器特有的状态袋（核心实现的空子类）。*WPF/Avalonia 已验证；其余各处形状相同（`*推断所得*`）。*

### 类：`StateSnapshot` — `.Property(...)` 重载集

每个重载都是 `StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`：

| 适配器 | 额外重载（除数值 + `System.Drawing.*` + `System.Numerics.*` 之外） |
|---|---|
| WPF | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` |
| Avalonia | `IInterpolable?`、`ITransform?`、`IBrush?`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` |
| WinUI | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` |
| MAUI | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` |
| WinForms | `IInterpolable?`、`Padding` |
| Razor | `string?`（无 `IInterpolable?`） |

## 命名空间：`VeloxDev.DynamicTheme`（各平台）

每个适配器都提供 `IThemeValueConverter` 实现。WPF（已验证）：`DoubleConverter`、`PointConverter`、`ThicknessConverter`、`CornerRadiusConverter`、`ColorConverter`、`BrushConverter`、`ObjectConverter` — 各自实现 `object? Convert(Type targetType, string propertyName, object?[] parameters)`。其他适配器提供相同的转换器集合（按同名文件 `*推断所得*`）。在动画主题切换前必须先调用一次 `ThemeManager.SetPlatformInterpolator(new Interpolator())`。

## 模板：`VeloxDev.WPF.Templates`（及同级包）

`dotnet new` 项模板。短名（在 `template.json` 中已验证）：

| 模板 | 短名 | 默认名 | 生成文件 |
|---|---|---|---|
| 节点视图 | `wpf-v-node` | `NodeView` | `TemplateClass.xaml/.cs` |
| 槽视图 | `wpf-v-slot` | `SlotView` | `TemplateClass.xaml/.cs` |
| 连接视图 | `wpf-v-link` | `LinkView` | `TemplateClass.xaml/.cs` |
| 树视图 | `wpf-v-tree` | `TreeView` | `TemplateClass.xaml/.cs` |
| 模板选择器 | `wpf-v-selector` | `TemplateSelector` | `TemplateClass.cs` |
| 网格装饰层 | `wpf-v-decorator` | `GridDecorator` | `TemplateClass.cs` |
| 小地图覆盖层 | `wpf-v-minimap` | `MinimapOverlay` | `TemplateClass.cs` |

样式别名（README 已验证；Avalonia/WinUI/MAUI 套件暴露相同选项）：

| 模板 | 样式别名 |
|---|---|
| 节点 | `-bg`、`-fg`、`-bb`、`-bt`、`-cr` |
| 槽 | `-bg`、`-sc`、`-bc`、`-sp` |
| 连接 | `-lc`、`-lt` |
| 树 | `-bg`、`-bb`、`-bt`、`-cr` |
| 网格装饰层 | `-bg`、`-mic`、`-mac`、`-ac`、`-gs`、`-mle`、`-rb`、`-rtc`、`-rlc`、`-rdc` |
| 小地图覆盖层 | `-bg`、`-bdr`、`-nf`、`-vs` |

所有模板用 `-ns` 指定生成的命名空间。
