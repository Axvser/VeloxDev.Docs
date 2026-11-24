# Hit testing and geometry

Adapters draw links with their own platform primitives, but hit testing must agree across them. `LinkCurve` is the flattened geometry a view publishes; `LinkHitTestEx` and `SlotHitTestEx` consume it in canvas coordinates.

## LinkCurve

```csharp
public sealed class LinkCurve
```

An immutable, arc-length-indexed polyline sampled from a cubic. The constructor is private; create a curve with a factory method.

### Properties and constants

| Member | Type | Description |
|---|---|---|
| `DefaultSampleCount` | `const int` | `128`; the default sample count for every builder. |
| `Count` | `int` | Number of sampled points. |
| `Bounds` | `WorkflowBounds` | Bounding box of the sampled points. |
| `Length` | `double` | Total arc length. |

### Point access

| Signature | Returns | Description |
|---|---|---|
| `XAt(int index)` | `double` | X of a sample. Not bounds-checked. |
| `YAt(int index)` | `double` | Y of a sample. Not bounds-checked. |
| `LengthAt(int index)` | `double` | Cumulative arc length at a sample. Not bounds-checked. |
| `PointAtLength(double length)` | `(double X, double Y)` | Arc-length interpolation, clamped to `[0, Length]`. |

### Factories

| Signature | Description |
|---|---|
| `static FromPoints(IReadOnlyList<double> xs, IReadOnlyList<double> ys)` | Builds a curve from matching coordinate lists. Throws `ArgumentNullException` for null lists and `ArgumentException` for a length mismatch. |
| `static BuildCubic(double startX, double startY, double endX, double endY, double pullMinimum, int sampleCount = DefaultSampleCount)` | Horizontal cubic; pull is `max(pullMinimum, |Δx| / 2)`. A non-positive sample count falls back to 128. |
| `static FromCubic(double p0X, double p0Y, double p1X, double p1Y, double p2X, double p2Y, double p3X, double p3Y, int sampleCount = DefaultSampleCount)` | Samples an explicit cubic. |
| `static LinkCurvePoints(ILinkComponent? link, double startX, double startY, double endX, double endY, double pullMinimum)` | Returns the control-point sequence along each port's outward normal; falls back to the horizontal rule when an end has no node. |
| `static BuildLinkCubic(ILinkComponent? link, double startX, double startY, double endX, double endY, double pullMinimum, int sampleCount = DefaultSampleCount)` | Samples the port-aware curve. |
| `static PortOutward(ISlotComponent slot)` | The slot's outward normal. Throws `ArgumentNullException` for a null slot. |
| `static PortOutward(double x, double y, INodeComponent? node)` | The outward normal at a point relative to a node; `(0,0)` when there is no node or its size is zero. |

### Hit test

| Signature | Returns | Description |
|---|---|---|
| `Contains(double x, double y, double radius)` | `bool` | Whether the point is within `radius` of the polyline. |

## ILinkHitTestable

```csharp
public interface ILinkHitTestable
{
    object? Visual { get; }
    LinkCurve? Curve { get; }
    void SetCurve(LinkCurve? curve, object? visual = null);
    bool Contains(double x, double y, double radius);
}
```

The per-link store behind the extension methods. The curve is a reference, not a copy; publishing `null` retracts it.

## LinkHitTestEx

```csharp
public static class LinkHitTestEx
{
    public const double DefaultHitRadius = 6d;

    public static ILinkHitTestable? HitTarget(this ILinkComponent link);
    public static void PublishCurve(this ILinkComponent link, LinkCurve? curve, object? visual = null);
    public static bool HitTest(this ILinkComponent link, double x, double y, double radius = DefaultHitRadius);
    public static ILinkComponent? HitTestVisibleLinks(this ITreeComponent tree, double x, double y, double radius = DefaultHitRadius);
}
```

| Member | Behaviour |
|---|---|
| `DefaultHitRadius` | 6 canvas units; the radius is not scaled by zoom. |
| `HitTarget` | Returns the link's curve store, creating it on first access. |
| `PublishCurve` | Stores the curve a view drew and an optional visual reference. |
| `HitTest` | Requires `link.IsVisible` and a published curve. |
| `HitTestVisibleLinks` | Walks `tree.GetHelper().VisibleItems` back-to-front, skips the virtual link, and skips points covered by a node. |

`HitTestVisibleLinks` is the standard right-press path for a link context menu. A link with no published curve is never hit.

## SlotHitTestEx

```csharp
public static class SlotHitTestEx
{
    public const double DefaultHitRadius = 12d;

    public static ISlotComponent? HitTest(ITreeComponent tree, double x, double y, double radius = DefaultHitRadius);
}
```

Finds the nearest slot within `radius` of a canvas point. Unlike the link helpers this is a static method, not an extension. It skips slots with NaN anchors, returns the nearest match, and throws `ArgumentNullException` for a null tree. The default radius is 12 canvas units.

## Notes

- All coordinates are canvas-local, the same space as `Anchor.Horizontal` and `Anchor.Vertical`.
- `LinkCurve.BuildLinkCubic` uses the sender and receiver slots to orient the handles; `BuildCubic` ignores the link and is the fallback.
- Publishing a new curve replaces the previous one. An adapter must republish after it redraws a link whose endpoints moved.
