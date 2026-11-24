# Surface navigation

Navigation is an optional capability an attached surface registers on the tree's route. Core supplies the contracts, one implementation that works against a narrow host, and `Locate()` extensions that need only model data.

## IWorkflowSurfaceScroller

```csharp
public interface IWorkflowSurfaceScroller
{
    void ScrollBy(double wheelDeltaX, double wheelDeltaY);
}
```

Called with the deltas of a wheel event. The horizontal positive is "right" and the vertical positive is "away from the user"; an implementation subtracts on the vertical axis. A zero delta leaves that axis untouched.

## IWorkflowSurfaceNavigator

```csharp
public interface IWorkflowSurfaceNavigator
{
    void CenterOn(double localX, double localY);
}
```

Centres a canvas-local point in the viewport. Zoom is not changed.

## ISurfaceScrollHost

```csharp
public interface ISurfaceScrollHost
{
    CanvasLayout? Layout { get; }
    double ViewportWidth { get; }
    double ViewportHeight { get; }
    double HorizontalOffset { get; }
    double VerticalOffset { get; }
    double HorizontalMaximum { get; }
    double VerticalMaximum { get; }
    SurfaceWheelProfile WheelProfile { get; }
    void ApplyOffset(double? horizontalOffset, double? verticalOffset);
    void ExpandCanvas();
}
```

The adapter's narrow seam. `Layout` may be `null`, in which case the scroller clamps without expanding the canvas. `ApplyOffset` leaves an axis untouched when its argument is `null`.

## SurfaceWheelProfile

```csharp
public readonly struct SurfaceWheelProfile
{
    public double DeltaPerNotch { get; init; }
    public double PixelsPerNotch { get; init; }
    public double ScrollLines { get; init; }
    public double LineHeight { get; init; }

    public static SurfaceWheelProfile FromLines(
        double deltaPerNotch, double scrollLines,
        double lineHeight = SurfaceScrollerCore.DefaultLineHeight);
    public static SurfaceWheelProfile FromPixels(double deltaPerNotch, double pixelsPerNotch);
}
```

| Member | Meaning |
|---|---|
| `DeltaPerNotch` | Raw wheel delta for one notch; must be positive or the implementation treats it as 1. |
| `PixelsPerNotch` | Pixels per notch; `0` selects the line-step mode. |
| `ScrollLines` | Lines per notch; a non-positive value means one viewport. |
| `LineHeight` | Pixels per line in line-step mode. |

`FromLines` configures the platform's own step. `FromPixels` configures a fixed pixel step.

## SurfaceScrollerCore

```csharp
public sealed class SurfaceScrollerCore : IWorkflowSurfaceScroller, IWorkflowSurfaceNavigator
```

The Core implementation of both contracts, written against `ISurfaceScrollHost`.

### Constants

| Constant | Value | Meaning |
|---|---:|---|
| `DefaultWheelDelta` | `120d` | One notch in raw wheel units. |
| `DefaultLineHeight` | `16d` | Pixels per line when the profile uses lines. |

### Methods

| Signature | Description |
|---|---|
| `SurfaceScrollerCore(ISurfaceScrollHost host)` | Throws `ArgumentNullException` when `host` is null. |
| `ScrollBy(double wheelDeltaX, double wheelDeltaY)` | Converts deltas through the host's profile, clamps, and expands the canvas on overscroll by `WorkflowSurfaceMath.DefaultPanExtendRatio` (0.15). A `(0,0)` delta is a no-op. |
| `CenterOn(double localX, double localY)` | Uses `WorkflowSurfaceMath.CenterScroll`, grows the canvas by the exact excess when the point cannot be centred, re-reads the maxima, and applies the clamped offsets. No-op when `Layout` is null. |

`ScrollBy` subtracts on the Y axis because a positive wheel delta means "away from the user" while a positive offset means "down". A caller mapping one axis onto the other flips the sign itself.

## WorkflowNavigationEx

```csharp
namespace VeloxDev.WorkflowSystem.StandardEx;

public static class WorkflowNavigationEx
{
    public static bool Locate(this INodeComponent node);
    public static bool Locate(this ISlotComponent slot);
    public static bool Locate(this ILinkComponent link);
}
```

`Locate()` reads model data only, so an off-screen node or an unmeasured slot can be centred before it has a view.

| Overload | Point centred |
|---|---|
| `Locate(INodeComponent)` | The node rectangle's centre. |
| `Locate(ISlotComponent)` | The parent node rectangle's centre; the slot's own `Anchor` is not read. |
| `Locate(ILinkComponent)` | The midpoint between the two endpoint nodes' centres; the published curve is not read. |

Each returns `false` and changes nothing when no `IWorkflowSurfaceNavigator` is registered or the target has no finite position. Each throws `ArgumentNullException` for a null argument. Zoom is preserved.

## Notes

- Both capabilities are `null` until an attached surface registers them, and are cleared when it detaches. Treat them as optional.
- The scroller expands the canvas rather than stopping at an edge. The maximum is re-read after the host adopts the new extent.
- `SurfaceScrollerCore` is also the navigator an adapter registers; one object usually fills both slots.
