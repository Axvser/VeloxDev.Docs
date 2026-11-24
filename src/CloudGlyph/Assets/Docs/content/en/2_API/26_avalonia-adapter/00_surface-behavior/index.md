# Surface behavior

`WorkflowSurfaceBehavior` resolves the surface's named parts, feeds the viewport, starts panning, hooks zoom, forwards pointer and key input, opens the link menu, and registers the scroll/navigation capabilities. Avalonia's version uses attached `AvaloniaProperty` values and tunnel wheel handlers.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.Avalonia`.

## WorkflowSurfaceBehavior

**Signature:** `sealed class WorkflowSurfaceBehavior : AvaloniaObject`

### Attached properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Master switch. |
| `ScrollViewerName` | `string?` | `null` | Scroll container whose offsets define the measured viewport. |
| `CanvasName` | `string?` | `null` | Canvas/panel the view pool fills. |
| `GridDecoratorName` | `string?` | `null` | Element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | Element whose blank-area press starts panning. |
| `MinimapOverlayName` | `string?` | `null` | Element implementing `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables the Ctrl+wheel zoom gesture. |
| `LinkMenuKey` | `string?` | `null` | Resource key of the link context menu. |

Each property is an `AttachedProperty<T>` registered on `UserControl` with the standard pair, for example `GetIsEnabled(AvaloniaObject)` / `SetIsEnabled(AvaloniaObject, bool)` and `GetScrollViewerName` / `SetScrollViewerName`.

`LinkMenuKey` raises a refresh on change because XAML property order can write it after `IsEnabled`. The menu is a keyed `ContextMenu`; the adapter sets the pressed link as its `DataContext`, opens it, and suspends `WorkflowInput` while it is open.

### Methods

| Method | Signature | Description |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | Re-resolves the named parts and rebinds the surface. |

A missing name disables that part silently.

### Lifecycle

- `IsEnabled = true` attaches: resolves names, captures the saved viewport, schedules one restore, reads the tree from `DataContext`, registers `Scroller` / `Navigator`, and subscribes.
- `IsEnabled = false` detaches and stops writing the model.
- The adapter registers wheel handlers with `RoutingStrategies.Tunnel`, because Avalonia has no `PreviewMouseWheel`; the host only supplies decisions it wants to change.

```csharp
var scope = new NameScope();
NameScope.SetNameScope(host, scope);
scope.RegisterName("PART_ScrollViewer", scrollViewer);
scope.RegisterName("PART_Canvas", canvas);
scope.RegisterName("PART_SurfaceBorder", border);

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetPointerPressSourceName(host, "PART_SurfaceBorder");
WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**Expected result:** scrolling writes `tree.GetHelper().Viewport`; a detached surface stops writing it.
