# Decorator contract

The surface behavior does not know how a grid is drawn. It knows one interface and one name: the element named by `GridDecoratorName` must implement `IWorkflowGridDecorator`, and the behavior pushes the current offsets into it once per layout, scroll, pan, or zoom pass.

## IWorkflowGridDecorator

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double RulerBand { get; }
}
```

| Member | Meaning |
|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | The surface `ScrollViewer`'s offsets, in scroll space. |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`, the canvas's own translation. |
| `RulerBand` | Thickness of the floating band overlapping the top and left content edges; `0` when there is no band. |

The four offsets are written by `SurfaceMetricsPush.PushGrid`; the decorator does not subscribe to anything. `RulerBand` is read-only on the interface because it is a function of the decorator's own configuration, not something the surface writes.

## SurfaceMetrics

```csharp
public readonly struct SurfaceMetrics
```

The grid consumes four members of the snapshot:

| Member | Type | Use |
|---|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Pushed as the decorator's scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Pushed as the decorator's content offsets. |
| `RulerBand` | `double` | Read from the decorator and used to build the free corner. |
| `Available` | `SurfaceAvailableArea` | Free corner for overlays; `Top` starts below the ruler band. |

`SurfaceMetrics` and `SurfaceMetrics.Create` are documented in full on [Surface math](../../07_canvas-input-navigation/03_surface-math/index.md).

## SurfaceMetricsPush.PushGrid

```csharp
public static void PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree);
```

1. Writes `ScrollOffsetX`, `ScrollOffsetY`, `ContentOffsetX`, and `ContentOffsetY` into the decorator.
2. Calls `tree.SetVirtualizeInset(left: decorator.RulerBand, top: decorator.RulerBand)`.

It throws `ArgumentNullException` for a null decorator; `tree` may be null.

The inset inflates the virtualization query without moving the authoritative viewport. A node visually under the ruler but inside the viewport is therefore kept. The minimap reads the same value as `AvailableTop`, so it starts below the band rather than over it.

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
```

The `Top` member is the grid-relevant one: `SurfaceMetrics.Create` sets it to `max(0, rulerBand)`, which is what moves the minimap and any other corner overlay below the ruler. Full members are on [Surface math](../../07_canvas-input-navigation/03_surface-math/index.md).

## Notes

- A decorator that draws a band must report the real `RulerBand`. Reporting `0` while drawing one culls nodes under the ruler one band too early and puts the minimap on top of the ruler.
- The push happens on every pass; the decorator only invalidates its own visual when a value changes.
- The interface is implemented by the drawing class, not by the adapter. The adapters only resolve the named part.
