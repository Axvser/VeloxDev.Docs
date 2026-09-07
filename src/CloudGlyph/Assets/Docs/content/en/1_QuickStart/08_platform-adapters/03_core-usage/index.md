# Platform Adapters — Core Usage

This page walks how the generated views interact with the workflow engine once they are hosted. Everything is shown on the WPF stack; the same attached behaviors exist under the same namespace on every adapter (see the feature overview).

## 1. Host a workflow tree

`WorkflowSurfaceBehavior` attaches to the surface **`UserControl`** (its `OnIsEnabledChanged` only handles `UserControl`s). Set its `IsEnabled`, name the inner parts through the attached string properties, and enable zoom:

```xml
<!-- Attributes placed on the surface host's root element (an excerpt of WorkflowView.xaml). -->
behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
```

Supply a workflow tree as the `DataContext` — an instance of an `IWorkflowTreeViewModel` produced by the `[WorkflowBuilder.Tree]` source generator (see the workflow-system Quick Start for building the tree):

```csharp
workflowView.DataContext = treeViewModel; // IWorkflowTreeViewModel
```

**Expected result:** dragging the blank background pans the surface (the behavior starts panning only on a blank hit-test, never on a node/slot/link), Ctrl + mouse-wheel zooms around the viewport center, and on every scroll the behavior updates `Helper.Viewport` and persists `Layout.ViewportOffset` in world coordinates.

## 2. Virtualize with `ViewPool`

The behavior object-pools item views. On the canvas set the attached `ItemsSource` to `Helper.VisibleItems` and give it the template selector:

```xml
<Canvas x:Name="PART_Canvas"
        Width="{Binding Layout.ActualSize.Width}"
        Height="{Binding Layout.ActualSize.Height}"
        Background="Transparent"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

`ViewPool` (an attached `DependencyObject`) pairs with `ViewManager`, which keeps a `Panel` and recycles views instead of destroying them: removed items are collapsed and their controls reused for newly visible items.

**Expected result:** only the nodes/links in the visible region are realized. In the WPF demo the "可见组件数" (visible items) counter stays small while the total node count grows.

## 3. Drag nodes and lay out slot anchors

`WorkflowNodeDragBehavior` moves the node; `WorkflowSlotLayoutBehavior` recomputes every slot's screen anchor whenever the canvas or the tree changes. The generated `NodeView` wires both:

```xml
<!-- Excerpt of NodeView.xaml: the root element and the header grid carry the behaviors. -->
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

**Expected result:** dragging the header executes `MoveCommand` with an `Offset` delta per mouse move (`node.MoveCommand.Execute(new Offset(dx, dy))`), and each slot's `Anchor` stays in sync with the collapsed canvas layout.

## 4. Connect slots

`WorkflowSlotConnectionBehavior` runs the connect commands on press/release. The generated `SlotView` keeps it enabled and mirrors the pointer handlers in code-behind:

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

**Expected result:** pressing an output slot and releasing over an input slot (or vice versa) creates a link; `SlotState` switches through `Sender` / `Receiver` flags and the `SlotView` recolors accordingly.

## 5. Grid decorator and minimap overlay

The surface behavior writes into two Core contracts on every layout/scroll pass: the decorator implements `IWorkflowGridDecorator` and the minimap `IWorkflowMinimapOverlay` (which extends the decorator contract with `ViewportWidth`, `ViewportHeight`, `WorkflowTree`, `IsMinimapVisible`). `WorkflowSurfaceBehavior.UpdateGridDecorator` also forwards `decorator.RulerBand` into `SetVirtualizeInset` so nodes under the ruler band are not culled.

Use the generated `GridDecorator` (grid + floating rulers) and the `MinimapOverlay` subclass of `WorkflowMinimapOverlay`; the minimap resolves the scroll viewer it drives through its own `ScrollViewerName`:

```xml
<local:MinimapOverlay x:Name="PART_MinimapOverlay"
                      HorizontalAlignment="Right"
                      VerticalAlignment="Top"
                      ScrollViewerName="PART_ScrollViewer" />
```

**Expected result:** the grid/ruler lines align to the pan (offset-driven), the minimap shows a thumbnail of the whole tree plus the viewport indicator, and dragging the minimap navigates the surface via the named `ScrollViewer`.

## 6. Per-platform transition and theme wiring

Every adapter closes the transition engine for its framework, and six of them also ship the dynamic-theme converters:

- `VeloxDev.TransitionSystem` — `Interpolator`, `State`, `Transition` / `Transition<T>`, `TransitionEffect`, `TransitionEffects` (`Empty`, `Theme` 0.46 s, `Hover` 0.32 s), `TransitionInterpreter`, `TransitionScheduler`, `UIThreadInspector`.
- `VeloxDev.DynamicTheme` — the platform converters (`ColorConverter`, `BrushConverter`, `ThicknessConverter`, `CornerRadiusConverter`, `PointConverter`, …) used by `ThemeConfig` attributes. WPF / Avalonia / WinUI / MAUI / WinForms / Razor each define their set under `PlatformAdapters/`; Jalium currently defines none (theme types live in Core).

Register the platform interpolator once at startup, then switch themes:

```csharp
ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**Expected result:** theme switches animate through the platform interpolator on the correct UI thread. The per-platform marshaling is: WPF via `Application.Current.Dispatcher` / the target `DispatcherObject`'s `Dispatcher`; Avalonia via `Dispatcher.UIThread`; WinUI via `DispatcherQueue` (captured on the UI thread, or taken from the target `DependencyObject`); MAUI via `Application.Current.Dispatcher`; WinForms/Razor via the captured `SynchronizationContext` (WinForms also prefers `Control.Invoke` / `BeginInvoke`); Jalium via `Dispatcher.MainDispatcher` / `Application.Current.Dispatcher`. WPF and Avalonia are exercised by the Transition/Theme demos; the remaining adapters' wiring is `*inferred*` from source.
