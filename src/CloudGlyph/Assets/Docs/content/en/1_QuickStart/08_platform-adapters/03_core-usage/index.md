# Platform Adapters — Core Usage

1) **Attach `WorkflowSurfaceBehavior` to the surface host.** Set `IsEnabled="True"` and name the inner parts via the attached string properties:

    ```xml
    behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
    behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
    behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
    behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
    behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
    behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
    ```

    **Expected result:** the host pans when the blank background is dragged, tracks the pointer via `SetPointerCommand`, updates `Helper.Viewport` and persists `Layout.ViewportOffset` on every scroll. (Demo: `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`.)

2) **Bind `ViewPool` to `Helper.VisibleItems` for virtualization.** On the canvas panel set the attached `ItemsSource` (plus a `TemplateSelector`):

    ```xml
    behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
    behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}"
    ```

    **Expected result:** only the visible nodes/links are materialized; removed items are collapsed and recycled by `ViewManager` instead of destroyed. (Demo: same `WorkflowView.xaml`.)

3) **Use `WorkflowNodeDragBehavior` and `WorkflowSlotConnectionBehavior` for drag & connect.** On the node's header grid: `behaviors:WorkflowNodeDragBehavior.IsEnabled="True"` + `CoordinateHostName="PART_Canvas"`. On each slot control: `behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True"`.

    **Expected result:** dragging the node header runs `MoveCommand` with the delta offset; pressing a slot runs `SendConnectionCommand` and releasing runs `ReceiveConnectionCommand`. (Demo: `SlotView.xaml`; template node view wires both.)

4) **Add the minimap overlay and the grid decorator.** Use the `wpf-v-minimap`/`wpf-v-decorator` outputs (`WorkflowMinimapOverlay` + `IWorkflowGridDecorator`). The surface behavior pushes scroll/content offsets into both interfaces on every layout change.

    **Expected result:** the minimap shows a thumbnail of all nodes plus the viewport indicator; dragging the indicator scrolls the surface; the grid decorator draws grid lines/rulers aligned to the content offset.

5) **Wire per-platform transitions and themes.** Each adapter exposes `Interpolator` (platform types registered in its static ctor), `TransitionEffects` (`Empty` / `Theme` 0.46 s / `Hover` 0.32 s), `ThemeValueConverters` and `UIThreadInspector` in the `VeloxDev.TransitionSystem` / `VeloxDev.DynamicTheme` namespaces. Call `ThemeManager.SetPlatformInterpolator(new Interpolator())` once, then `ThemeManager.Transition<Light>(TransitionEffects.Theme)`.

    **Expected result:** animated theme switches and smooth transitions run on the correct UI thread (`Application.Current.Dispatcher` for WPF, `Dispatcher.UIThread` for Avalonia, `Application.Current.Dispatcher` for MAUI, `SynchronizationContext` for WinForms/Razor; WinUI marshals through `DispatcherQueue`). WPF/Avalonia are exercised by the Transition/Theme demos; the other adapters' wiring is *inferred* from source.
