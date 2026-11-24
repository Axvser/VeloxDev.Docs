# Surface and pool

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Class: WorkflowSurfaceBehavior

`public static class WorkflowSurfaceBehavior`

Attached configuration for the Jalium surface. It hosts named parts; it is not a control to derive from. The tree comes from the host's `DataContext`.

### Constants

| Member | Type | Value |
| --- | --- | --- |
| `TemplateSelectorKey` | `string` | `"WorkflowTemplateSelector"` |
| `CanvasWidth` | `double` | `2000` |
| `CanvasHeight` | `double` | `2000` |

`CanvasWidth` and `CanvasHeight` are lower bounds so a nearly empty tree still has a pannable surface.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `ScrollViewerNameProperty` | `string?` | `null` | `GetScrollViewerName`, `SetScrollViewerName` |
| `CanvasNameProperty` | `string?` | `null` | `GetCanvasName`, `SetCanvasName` |
| `GridDecoratorNameProperty` | `string?` | `null` | `GetGridDecoratorName`, `SetGridDecoratorName` |
| `PointerPressSourceNameProperty` | `string?` | `null` | `GetPointerPressSourceName`, `SetPointerPressSourceName` |
| `MinimapOverlayNameProperty` | `string?` | `null` | `GetMinimapOverlayName`, `SetMinimapOverlayName` |
| `ZoomEnabledProperty` | `bool` | `false` | `GetZoomEnabled`, `SetZoomEnabled` |
| `CanvasTransformProperty` | `Transform?` | `null` | `GetCanvasTransform`, `SetCanvasTransform` |
| `LinkMenuKeyProperty` | `string?` | `null` | `GetLinkMenuKey`, `SetLinkMenuKey` |

All accessors take a `DependencyObject`; none throws.

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `Refresh(FrameworkElement host)` | `void` | Re-resolves named parts, canvas size, layout, viewport restoration and overlays. |
| `NavigateToCanvasLocal(FrameworkElement host, double localX, double localY)` | `void` | Centers the view on a canvas-local point, growing the canvas at an edge. |
| `NotifyZoomCommitted(FrameworkElement host)` | `void` | Re-runs virtualization using the viewer's current offsets. |
| `NotifyZoomCommitted(FrameworkElement host, double horizontalOffset, double verticalOffset)` | `void` | Re-runs virtualization against a committed scroll target. Use `double.NaN` to read the viewer's value. |
| `TreeOf(DependencyObject element)` | `ITreeComponent?` | Returns the tree bound to the surface host. |

No exception is declared.

### Example

```xml
<UserControl xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.Jalium"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu" />
```

### Notes

- Keep the tree's plain `CanvasTransform` mirror. Without it, every card stays at the world origin after a pan, with no error.
- `NotifyZoomCommitted` arms a short zoom pin so a stale pre-commit `ScrollChanged` cannot overwrite the target viewport, then re-measures slot anchors inline.
- The whole grid renderer is template-owned: `GridDecorator` implements `IWorkflowGridDecorator`; the adapter ships no grid class.

## Class: ViewPool

`public static class ViewPool`

Attached pool for a Jalium `Panel`. The Core pipeline is `ViewSourcePipeline`.

### Properties

| Member | Type | Accessors |
| --- | --- | --- |
| `ItemsSourceProperty` | `DependencyProperty` (`INotifyCollectionChanged`) | `GetItemsSource` / `SetItemsSource` |
| `TemplateSelectorProperty` | `DependencyProperty` (`DataTemplateSelector`) | `GetTemplateSelector` / `SetTemplateSelector` |

All accessors take a `Panel`. Changing either property disposes the running system and rebuilds it; there is no incremental re-template path.

### Example

```xml
<Canvas x:Name="PART_Canvas" Background="Transparent"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

### Notes

- The panel's `Unloaded` event disposes the system, so a removed surface does not keep the tree alive.
- A `null` source disposes the running system and materializes nothing until a source is set again.
