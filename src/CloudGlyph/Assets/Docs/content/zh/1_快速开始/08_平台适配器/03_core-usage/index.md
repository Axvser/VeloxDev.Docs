# 平台适配器 — 核心用法

1) **给画布宿主附加 `WorkflowSurfaceBehavior`。** 设置 `IsEnabled="True"` 并通过附加字符串属性命名内部部件：

    ```xml
    behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
    behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
    behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
    behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
    behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
    behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
    ```

    **预期结果：** 拖拽空白背景可以平移画布；`SetPointerCommand` 跟踪指针；每次滚动都会更新 `Helper.Viewport` 并持久化 `Layout.ViewportOffset`。（演示：`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`。）

2) **把 `ViewPool` 绑定到 `Helper.VisibleItems` 实现虚拟化。** 在画布面板上设置附加的 `ItemsSource`（外加 `TemplateSelector`）：

    ```xml
    behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
    behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}"
    ```

    **预期结果：** 只实例化可见的节点/连接；被移除的项由 `ViewManager` 折叠并回收复用，而不是销毁重建。（演示：同一个 `WorkflowView.xaml`。）

3) **用 `WorkflowNodeDragBehavior` 和 `WorkflowSlotConnectionBehavior` 实现拖拽与连线。** 在节点标题栏网格上：`behaviors:WorkflowNodeDragBehavior.IsEnabled="True"` + `CoordinateHostName="PART_Canvas"`。在每个槽控件上：`behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True"`。

    **预期结果：** 拖拽节点标题执行 `MoveCommand`（增量偏移）；按下槽执行 `SendConnectionCommand`，松开执行 `ReceiveConnectionCommand`。（演示：`SlotView.xaml`；模板节点视图两个行为都已接好。）

4) **添加小地图覆盖层与网格装饰层。** 使用 `wpf-v-minimap`/`wpf-v-decorator` 的输出（`WorkflowMinimapOverlay` + `IWorkflowGridDecorator`）。每次布局变化时画布行为都会把滚动/内容偏移推给这两个接口。

    **预期结果：** 小地图显示所有节点缩略图以及视口指示框；拖拽指示框可滚动画布；网格装饰层按内容偏移绘制网格线/标尺。

5) **接好各平台的过渡与主题。** 每个适配器都在 `VeloxDev.TransitionSystem` / `VeloxDev.DynamicTheme` 命名空间暴露 `Interpolator`（静态构造函数注册平台类型）、`TransitionEffects`（`Empty` / `Theme` 0.46 秒 / `Hover` 0.32 秒）、`ThemeValueConverters` 和 `UIThreadInspector`。先调用一次 `ThemeManager.SetPlatformInterpolator(new Interpolator())`，再 `ThemeManager.Transition<Light>(TransitionEffects.Theme)`。

    **预期结果：** 主题切换与过渡动画在正确的 UI 线程上执行（WPF 用 `Application.Current.Dispatcher`，Avalonia 用 `Dispatcher.UIThread`，MAUI 用 `Application.Current.Dispatcher`，WinForms/Razor 用 `SynchronizationContext`；WinUI 通过 `DispatcherQueue` 编组）。WPF/Avalonia 由 Transition/Theme 演示覆盖；其余适配器的接线为*推断所得*。
