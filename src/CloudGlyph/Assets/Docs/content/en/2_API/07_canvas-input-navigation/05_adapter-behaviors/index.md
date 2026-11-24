# Adapter behaviors

The WPF adapter closes the input route with four attached-property hosts. They resolve named parts, translate native gestures into model commands, and publish the render transform templates bind to. The other six adapters expose the same role set through their own property system; the WPF signatures below are the reference shape.

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## WorkflowSurfaceBehavior

```csharp
public sealed class WorkflowSurfaceBehavior : DependencyObject
```

Attaches to the host `UserControl`. It sets `Focusable = true` on the host, registers a `SurfaceScrollerCore` as both scroller and navigator, and owns pan, Ctrl+wheel zoom, and wheel arbitration.

### Attached properties

| Property | Type | Default | Meaning |
|---|---|---:|---|
| `IsEnabled` | `bool` | `false` | Turns the surface on. |
| `ScrollViewerName` | `string?` | `null` | Named `ScrollViewer` to measure and scroll. |
| `CanvasName` | `string?` | `null` | Named `Canvas` that is the pointer reference frame. |
| `GridDecoratorName` | `string?` | `null` | Named `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | Element that receives presses; blank-surface pan starts there. |
| `MinimapOverlayName` | `string?` | `null` | Named `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables Ctrl+wheel zoom. |
| `LinkMenuKey` | `string?` | `null` | Resource key of the link context menu. |

### Accessors and methods

| Signature | Description |
|---|---|
| `GetIsEnabled` / `SetIsEnabled(DependencyObject, bool)` | Reads or writes `IsEnabled`. |
| `GetScrollViewerName` / `SetScrollViewerName` | Reads or writes the scroll-viewer name. |
| `GetCanvasName` / `SetCanvasName` | Reads or writes the canvas name. |
| `GetGridDecoratorName` / `SetGridDecoratorName` | Reads or writes the decorator name. |
| `GetPointerPressSourceName` / `SetPointerPressSourceName` | Reads or writes the press-source name. |
| `GetMinimapOverlayName` / `SetMinimapOverlayName` | Reads or writes the minimap name. |
| `GetZoomEnabled` / `SetZoomEnabled` | Reads or writes the zoom switch. |
| `GetLinkMenuKey` / `SetLinkMenuKey` | Reads or writes the menu resource key. |
| `static Refresh(UserControl host)` | Re-resolves the named parts and re-applies layout. Call after replacing content or swapping a tree. |

Zoom multiplies `Layout.Scale` by `1/1.1` or `1.1` and clamps to `0.1`–`10`. Pan grows the canvas through `WorkflowSurfaceMath.ClampScrollOffset` with `DefaultPanExtendRatio`. `GetPressHandle` is internal; the drag and connection behaviors use it to honour a press a subscriber already prevented.

## WorkflowCanvasTransformBehavior

```csharp
public static class WorkflowCanvasTransformBehavior
```

Publishes the transform the surface computes for node and link views.

| Member | Type | Default | Description |
|---|---|---|---|
| `Transform` | `Transform?` (attached) | `null` | The current render transform. |
| `GetTransform(UIElement)` / `SetTransform(UIElement, Transform?)` | — | — | Attached accessors. |

A node or link template binds `RenderTransform` to this property. Without that binding, items render at world coordinates and ignore pan and zoom. `Apply` is internal; the surface writes the value.

## WorkflowNodeDragBehavior

```csharp
public sealed class WorkflowNodeDragBehavior : DependencyObject
```

Attached to the draggable part of a node view. It hooks left-button press, move, release, and lost capture, and skips a drag whose press handle already has `PreventDefault`.

| Property | Type | Default | Meaning |
|---|---|---|---|
| `IsEnabled` | `bool` | `false` | Turns drag on for this view. |
| `CoordinateHostName` | `string?` | `null` | Canvas whose coordinates the delta is measured in. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host; falls back to `typeof(Canvas)`. |

Accessors are the standard `GetIsEnabled`/`SetIsEnabled`, `GetCoordinateHostName`/`SetCoordinateHostName`, and `GetCoordinateHostType`/`SetCoordinateHostType` pairs on `DependencyObject`.

Without a coordinate host, the behavior uses the nearest ancestor `Canvas`.

## WorkflowSlotConnectionBehavior

```csharp
public sealed class WorkflowSlotConnectionBehavior : DependencyObject
```

Attached to a slot view. A left press executes `SendConnectionCommand`; a left release executes `ReceiveConnectionCommand`. The control's `DataContext` must be an `ISlotComponent`.

| Property | Type | Default | Meaning |
|---|---|---|---|
| `IsEnabled` | `bool` | `false` | Turns connection gestures on for this view. |

Accessors: `GetIsEnabled(DependencyObject)` and `SetIsEnabled(DependencyObject, bool)`.

A press the surface already prevented does not start a connection. Connection drags are not undoable by design; the resulting structural edit is what enters history.

## Notes

- Every name is resolved in the `UserControl` namescope. A part in another namescope is not found.
- `GridDecoratorName` and `MinimapOverlayName` are optional hooks for the features that own those overlays.
- `Refresh` is the recovery path when parts appear after the surface loads.
