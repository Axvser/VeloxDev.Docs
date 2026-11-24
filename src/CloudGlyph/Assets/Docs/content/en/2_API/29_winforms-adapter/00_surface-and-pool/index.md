# Surface and view pool

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Class: WorkflowSurfaceBehavior

`public sealed class WorkflowSurfaceBehavior`

Static attached configuration for the Easel surface. The host must be a `VisualHost`; enabling the behavior attaches the camera, resolves the named parts, binds the tree and starts the input route.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `ZoomEnabledProperty` | `bool` | `false` | `GetZoomEnabled`, `SetZoomEnabled` |
| `ScrollViewerNameProperty` | `string?` | `null` | `GetScrollViewerName`, `SetScrollViewerName` |
| `CanvasNameProperty` | `string?` | `null` | `GetCanvasName`, `SetCanvasName` |
| `GridDecoratorNameProperty` | `string?` | `null` | `GetGridDecoratorName`, `SetGridDecoratorName` |
| `MinimapOverlayNameProperty` | `string?` | `null` | `GetMinimapOverlayName`, `SetMinimapOverlayName` |
| `SurfaceNameProperty` | `string?` | `null` | `GetSurfaceName`, `SetSurfaceName` |
| `PointerPressSourceNameProperty` | `string?` | `null` | `GetPointerPressSourceName`, `SetPointerPressSourceName` |
| `VisualTemplateSelectorProperty` | `VisualTemplateSelector?` | `null` | `GetVisualTemplateSelector`, `SetVisualTemplateSelector` |
| `VisualTemplateSelectorKeyProperty` | `string?` | `"WorkflowTemplateSelector"` | `GetVisualTemplateSelectorKey`, `SetVisualTemplateSelectorKey` |
| `VisualLinkColorProperty` | `System.Drawing.Color` | `#DDFFFFFF` | `GetVisualLinkColor`, `SetVisualLinkColor` |
| `VisualLinkThicknessProperty` | `float` | `2` | `GetVisualLinkThickness`, `SetVisualLinkThickness` |
| `VisualLinkHoverColorProperty` | `System.Drawing.Color` | `White` | `GetVisualLinkHoverColor`, `SetVisualLinkHoverColor` |
| `VisualLinkHoverThicknessProperty` | `float` | `3.5` | `GetVisualLinkHoverThickness`, `SetVisualLinkHoverThickness` |
| `VisualLinkVirtualColorProperty` | `System.Drawing.Color` | `#DDFFFFFF` | `GetVisualLinkVirtualColor`, `SetVisualLinkVirtualColor` |
| `VisualLinkGlowProperty` | `bool` | `false` | `GetVisualLinkGlow`, `SetVisualLinkGlow` |
| `WorkflowTreeProperty` | `ITreeComponent?` | `null` | `GetWorkflowTree`, `SetWorkflowTree` |
| `LinkMenuBuilderProperty` | `Action<ContextMenuStrip, ILinkComponent>?` | `null` | `GetLinkMenuBuilder`, `SetLinkMenuBuilder` |
| `LinkMenuKeyProperty` | `string?` | `null` | `GetLinkMenuKey`, `SetLinkMenuKey` |

Every `Get`/`Set` takes a `System.Windows.Forms.Control` and throws `ArgumentNullException` when the control is `null`.

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `Refresh(Control host)` | `void` | Re-reads parts, tree, selector and camera, then re-ensures the attached behaviors. |
| `GetZoom(Control host)` | `double` | Current camera scale; `1` means world units equal surface units. |
| `GetPan(Control host)` | `PointF` | Signed pan translation applied after scaling. |
| `SetPan(Control host, PointF pan)` | `void` | Sets the pan translation and re-applies the camera. |
| `SurfaceToWorld(Control host, PointF surfacePoint)` | `PointF` | Converts a host-surface point to world coordinates. |
| `WorldToSurface(Control host, PointF worldPoint)` | `PointF` | Converts a world point to host-surface coordinates. |
| `GetWorldViewport(Control host)` | `Offset` | Top-left of the visible region in world coordinates. |
| `SetWorldViewport(Control host, Offset worldOffset)` | `void` | Moves the camera so the visible region starts at `worldOffset`. |
| `ZoomAt(Control host, PointF surfacePoint, double factor)` | `void` | Zooms around a surface point, clamped to `0.1`–`10`, keeping that world point fixed. |
| `ProcessWheel(Control host, PointF surfacePoint, int delta, Keys modifiers)` | `bool` | Routes one wheel turn; `false` when no tree is bound. |

`Unknown` exceptions are not declared. `ProcessWheel` accepts the raw wheel delta (one notch = 120). Ctrl+wheel zooms when `ZoomEnabled` is set; otherwise the turn goes to `WorkflowInput.Scroller`.

### Example

```csharp
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
WorkflowSurfaceBehavior.SetWorkflowTree(host, tree);
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
// Source: Demo
```

### Notes

- The tree does not arrive through `DataContext` on the tested target; `SetWorkflowTree` binds it explicitly. `DataContext` is still read on `net8.0-windows` and later, and `Tag` on older target frameworks.
- Setting `SurfaceName` restricts part lookup to a subtree when the visual root also carries a workbench shell.
- `PointerPressSourceName` exists for WPF parity. Input is routed by the visual host, not by a named press source.

## Class: ViewPool

`public sealed class ViewPool`

Attached pool over an `INotifyCollectionChanged` source. The pool bookkeeping lives in Core; `ViewSourcePipeline` closes the Easel layers.

### Properties and event

| Member | Type | Description |
| --- | --- | --- |
| `ItemsSourceProperty` | `DependencyProperty` | Attached source; normally `Helper.VisibleItems`. |
| `TemplateSelectorProperty` | `DependencyProperty` | Attached `VisualTemplateSelector`. |
| `Changed` | `event EventHandler<ViewPoolChangedEventArgs>?` | Raised once after a materialization batch on a host. |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `GetItemsSource(VisualElement element)` | `INotifyCollectionChanged?` | Reads the attached source. |
| `SetItemsSource(VisualElement element, INotifyCollectionChanged? value)` | `void` | Sets the source. `null` disposes the running system; replacing it rebuilds in place. |
| `GetTemplateSelector(VisualElement element)` | `VisualTemplateSelector?` | Reads the attached selector. |
| `SetTemplateSelector(VisualElement element, VisualTemplateSelector? value)` | `void` | Sets the selector and rebuilds a running system. |
| `GetActiveViewCount(VisualElement host)` | `int` | Number of items with a bound view. |
| `GetPendingCount(VisualElement host)` | `int` | Number of items waiting for a scheduled batch. |
| `Refresh(VisualElement host)` | `void` | Disposes the previous system and materializes the current source. |

`Refresh` throws `ArgumentNullException` for a `null` host. The attached setters do not throw; a non-panel element only stores the value.

### Example

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

## Class: ViewPoolChangedEventArgs

`public sealed class ViewPoolChangedEventArgs(VisualElement host) : EventArgs`

| Member | Type | Description |
| --- | --- | --- |
| `Host` | `VisualElement` | The canvas whose pooled views changed. |

## Class: WorkflowEvents

`public sealed class WorkflowEvents`

Attached event sinks. The value is an `INodeEventSink`, `ISlotEventSink` or `ITreeEventSink`; forwarding is shared through `WorkflowEventRelay`.

| Member | Type | Accessors |
| --- | --- | --- |
| `NodeProperty` | `DependencyProperty` (`INodeEventSink`) | `GetNode` / `SetNode` |
| `SlotProperty` | `DependencyProperty` (`ISlotEventSink`) | `GetSlot` / `SetSlot` |
| `TreeProperty` | `DependencyProperty` (`ITreeEventSink`) | `GetTree` / `SetTree` |

`Get*`/`Set*` take a `VisualElement`. `Ensure(VisualElement element)` attaches a relay and connects the current sinks to the current data context.

### Example

```xml
<local:NodeView behaviors:WorkflowEvents.Node="{Binding NodeEvents}" />
```

### Notes

- The subscription follows `DataContext`, so a recycled pooled view drops the old component and connects the new one.
- When an element's sinks or data context are unchanged, `Ensure` does not re-subscribe.
