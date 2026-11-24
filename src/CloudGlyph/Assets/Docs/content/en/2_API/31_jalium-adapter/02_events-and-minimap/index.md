# Events and minimap

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Class: WorkflowEvents

`public static class WorkflowEvents`

Attached event sinks. The value is an `INodeEventSink`, `ISlotEventSink` or `ITreeEventSink`; forwarding is shared through `WorkflowEventRelay`.

### Attached properties

| Property field | CLR type | Accessors |
| --- | --- | --- |
| `NodeProperty` | `INodeEventSink?` | `GetNode`, `SetNode` |
| `SlotProperty` | `ISlotEventSink?` | `GetSlot`, `SetSlot` |
| `TreeProperty` | `ITreeEventSink?` | `GetTree`, `SetTree` |

All accessors take a `DependencyObject` and do not throw.

### Example

```xml
<local:NodeView behaviors:WorkflowEvents.Node="{Binding NodeEvents}" />
```

### Notes

- The subscription follows `DataContext`. A pooled view handed to another node drops the old subscription and connects the new one.
- `Unloaded` disconnects all three lines so the element does not root the component.

## Class: WorkflowMinimapOverlay

`public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay`

Self-contained minimap. It maps the bounding box of all node cards into the minimap, draws a translucent viewport rectangle clamped inside it, and drags to pan by reusing the surface's edge-aware navigation. Tree subscription, mapping, placement and drag math live in the Core `MinimapPipeline`.

### Properties

| Property field / property | CLR type | Default |
| --- | --- | --- |
| `ScrollOffsetX` | `double` | `0` |
| `ScrollOffsetY` | `double` | `0` |
| `ContentOffsetX` | `double` | `0` |
| `ContentOffsetY` | `double` | `0` |
| `ViewportWidth` | `double` | `0` |
| `ViewportHeight` | `double` | `0` |
| `IsMinimapVisible` | `bool` | `true` |
| `MinimapMargin` | `double` | `12` |
| `AvailableRight` | `double` | `0` |
| `AvailableTop` | `double` | `0` |
| `AvailableBottom` | `double` | `0` |
| `WorkflowTree` | `ITreeComponent?` | `null` |
| `MinimapWidth` | `double` | `200` |
| `MinimapHeight` | `double` | `140` |
| `MinimapMinSize` | `double` | `1` |
| `ContentPadding` | `double` | `8` |
| `MinimapBackground` | `Brush` | translucent dark fill |
| `MinimapBorderBrush` | `Brush` | `#DC94A3B8` |
| `MinimapBorderThickness` | `double` | `1` |
| `MinimapCornerRadius` | `double` | `4` |
| `NodeBrush` | `Brush` | `#DC38BDF8` |
| `NodeCornerRadius` | `double` | `2` |
| `ViewportFill` | `Brush` | `#30FFFFFF` |
| `ViewportStroke` | `Brush` | `#F0FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1` |
| `ScrollViewerName` | `string?` | `null` |
| `ScrollViewer` | `ScrollViewer?` | `null` |
| `RulerBand` | `double` (get) | always `0` |

Most properties have a matching `...Property` field. `ScrollViewer` is a plain CLR property assigned by the composing control for drag-to-pan; `ScrollViewerName` names the viewer in the template's name scope.

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `NavigateToCanvasLocal(double wx, double wy)` | `void` | Centers the surface on a canvas-local point. |

### Extension point

`protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context)` draws the default nodes and viewport block. Override and call `base` to add to it.

### Notes

- Only the minimap rectangle is hit-testable; the rest of the overlay lets pointer input through.
- Dragging past an edge grows `CanvasLayout.PositiveOffset` / `NegativeOffset`, matching the surface's navigation.
