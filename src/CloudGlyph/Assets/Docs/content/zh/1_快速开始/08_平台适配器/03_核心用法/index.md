# 平台适配器 — 核心用法

本页讲解生成的视图被宿主起来后，如何与工作流引擎交互。全部以 WPF 技术栈演示；同样的附加行为在其它适配器的同一命名空间下都存在（见特性概览）。

## 1. 宿主一棵工作流树

`WorkflowSurfaceBehavior` 附加到表面 **`UserControl`**（它的 `OnIsEnabledChanged` 只处理 `UserControl`）。设置 `IsEnabled`，用附加字符串属性命名内部部件，并开启缩放：

```xml
<!-- 放在表面宿主根元素上的属性（WorkflowView.xaml 的摘录）。 -->
behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
```

把一棵工作流树作为 `DataContext` 供上——也就是由 `[WorkflowBuilder.Tree]` 源生成器产生的 `IWorkflowTreeViewModel` 实例（构树部分见「工作流系统」快速开始）：

```csharp
workflowView.DataContext = treeViewModel; // IWorkflowTreeViewModel
```

**预期结果：** 拖拽空白背景会平移画布（行为只在空白的命中测试上开始平移，绝不在节点/槽/连线上）；Ctrl + 鼠标滚轮围绕视口中心缩放；每次滚动行为都会更新 `Helper.Viewport`，并把 `Layout.ViewportOffset` 以世界坐标持久化。

## 2. 用 `ViewPool` 虚拟化

行为把项视图对象池化。在画布上设置附加的 `ItemsSource` 为 `Helper.VisibleItems`，并给出模板选择器：

```xml
<Canvas x:Name="PART_Canvas"
        Width="{Binding Layout.ActualSize.Width}"
        Height="{Binding Layout.ActualSize.Height}"
        Background="Transparent"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

`ViewPool`（附加的 `DependencyObject`）与 `ViewManager` 配对：`ViewManager` 持有一个 `Panel` 并复用视图而不是销毁重建——被移除的项会折叠，其控件被新出现的可见项复用。

**预期结果：** 只有可见区域内的节点/连线被实例化。在 WPF 演示里，「可见组件数」计数器会保持很小，而节点总数可以很大。

## 3. 拖拽节点与槽锚点布局

`WorkflowNodeDragBehavior` 移动节点；`WorkflowSlotLayoutBehavior` 在画布或树每次变化时重算每个槽的屏幕锚点。生成的 `NodeView` 同时接好两者：

```xml
<!-- NodeView.xaml 摘录：根元素与头部网格承载行为。 -->
<UserControl x:Class="Demo.Views.Workflow.NodeView"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
             behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
             behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
             behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">

    <Grid behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas"
          behaviors:WorkflowNodeDragBehavior.IsEnabled="True">
        <TextBlock Text="{Binding Name}" />
    </Grid>

</UserControl>
```

**预期结果：** 拖拽头部时，每次鼠标移动都对节点执行 `MoveCommand`（增量偏移：`node.MoveCommand.Execute(new Offset(dx, dy))`），且每个槽的 `Anchor` 与塌缩后的画布布局保持同步。

## 4. 连接槽

`WorkflowSlotConnectionBehavior` 在按下/松开时执行连接命令。生成的 `SlotView` 保持它启用，并在 code-behind 里镜像同样的指针处理器：

```xml
<UserControl x:Class="Demo.Views.Workflow.SlotView"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True"
             MouseLeftButtonUp="OnPointerReleased"
             MouseLeftButtonDown="OnPointerPressed">
```

```csharp
private void OnPointerPressed(object sender, MouseButtonEventArgs e)
{
    if (DataContext is IWorkflowSlotViewModel context)
    {
        context.SendConnectionCommand.Execute(null);
    }
    e.Handled = true;
}

private void OnPointerReleased(object sender, MouseButtonEventArgs e)
{
    if (DataContext is IWorkflowSlotViewModel context)
    {
        context.ReceiveConnectionCommand.Execute(null);
    }
    e.Handled = true;
}
```

**预期结果：** 按下输出槽并在输入槽上松开（或反过来）会创建一条连线；`SlotState` 在 `Sender` / `Receiver` 标志间切换，`SlotView` 相应换色。

## 5. 网格装饰层与小地图覆盖层

每次布局/滚动时，表面行为会写入两个 Core 契约：装饰层实现 `IWorkflowGridDecorator`，小地图实现 `IWorkflowMinimapOverlay`（它继承装饰层契约，另加 `ViewportWidth`、`ViewportHeight`、`WorkflowTree`、`IsMinimapVisible`）。`WorkflowSurfaceBehavior.UpdateGridDecorator` 还会把 `decorator.RulerBand` 转发给 `SetVirtualizeInset`，避免标尺带下方的节点被过早剔除。

用生成的 `GridDecorator`（网格 + 浮动标尺）与 `WorkflowMinimapOverlay` 的 `MinimapOverlay` 子类；小地图通过自身的 `ScrollViewerName` 找到要驱动的滚动器：

```xml
<local:MinimapOverlay x:Name="PART_MinimapOverlay"
                      HorizontalAlignment="Right"
                      VerticalAlignment="Top"
                      ScrollViewerName="PART_ScrollViewer" />
```

**预期结果：** 网格/标尺线随平移对齐（由偏移驱动）；小地图显示整棵树的缩略图与视口指示框；在小地图上拖拽会通过命名的 `ScrollViewer` 导航画布。

## 6. 各平台过渡与主题接线

每个适配器都为自己的框架封闭过渡引擎，其中六个还提供动态主题转换器：

- `VeloxDev.TransitionSystem` — `Interpolator`、`State`、`Transition` / `Transition<T>`、`TransitionEffect`、`TransitionEffects`（`Empty`、`Theme` 0.46 秒、`Hover` 0.32 秒）、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector`。
- `VeloxDev.DynamicTheme` — 平台转换器（`ColorConverter`、`BrushConverter`、`ThicknessConverter`、`CornerRadiusConverter`、`PointConverter` 等），供 `ThemeConfig` 属性使用。WPF / Avalonia / WinUI / MAUI / WinForms / Razor 各自在 `PlatformAdapters/` 下定义转换器集；Jalium 目前没有定义（主题类型位于 Core）。

启动时注册一次平台插值器，然后切换主题：

```csharp
ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**预期结果：** 主题切换通过平台插值器在正确的 UI 线程上动画完成。各平台的编组方式：WPF 经 `Application.Current.Dispatcher` / 目标 `DispatcherObject` 自己的 `Dispatcher`；Avalonia 经 `Dispatcher.UIThread`；WinUI 经 `DispatcherQueue`（在 UI 线程捕获，或取自目标 `DependencyObject`）；MAUI 经 `Application.Current.Dispatcher`；WinForms/Razor 经捕获的 `SynchronizationContext`（WinForms 还优先用 `Control.Invoke` / `BeginInvoke`）；Jalium 经 `Dispatcher.MainDispatcher` / `Application.Current.Dispatcher`。WPF 与 Avalonia 由 Transition/Theme 演示覆盖；其余适配器的接线为 `*推断所得*`。
