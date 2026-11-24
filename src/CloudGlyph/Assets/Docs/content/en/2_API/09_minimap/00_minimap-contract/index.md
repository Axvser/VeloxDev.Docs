# Minimap contract

The minimap is fed by the surface behavior and composed from three platform layers. The contracts below are the whole exchange.

## IWorkflowMinimapOverlay

```csharp
public interface IWorkflowMinimapOverlay : IWorkflowGridDecorator
{
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    ITreeComponent? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
    double AvailableRight { get; set; }
    double AvailableTop { get; set; }
    double AvailableBottom { get; set; }
    double MinimapMargin { get; set; }
}
```

It derives from `IWorkflowGridDecorator`, so it also carries `ScrollOffsetX`, `ScrollOffsetY`, `ContentOffsetX`, `ContentOffsetY`, and the read-only `RulerBand`.

| Member | Meaning |
|---|---|
| `ViewportWidth` / `ViewportHeight` | Viewport size in the surface's scroll space, used to scale the indicator and resolve drags. |
| `WorkflowTree` | Tree whose nodes the minimap renders. |
| `IsMinimapVisible` | Whether a pass draws anything. |
| `AvailableRight` | X of the usable right edge, excluding the vertical scrollbar. |
| `AvailableTop` | Y of the usable top edge, below the ruler band. |
| `AvailableBottom` | Y of the usable bottom edge, excluding the horizontal scrollbar. |
| `MinimapMargin` | Gap kept from the available corner. |

The surface behavior writes every member before each render pass. The minimap itself reads them; a host does not normally set them by hand.

## IMinimapRenderer<TSurface>

```csharp
public interface IMinimapRenderer<TSurface>
{
    void Render(TSurface surface, MinimapDrawContext context);
}
```

Draws one pass: the frame, every rectangle in `context.MappedNodes`, and the viewport indicator in `context.MappedViewport`. The default adapter renderer does not draw links.

## IMinimapViewportHost

```csharp
public interface IMinimapViewportHost
{
    double ScrollOffsetX { get; }
    double ScrollOffsetY { get; }
    double ContentOffsetX { get; }
    double ContentOffsetY { get; }
    double ViewportWidth { get; }
    double ViewportHeight { get; }
    double ScrollableWidth { get; }
    double ScrollableHeight { get; }
    void ApplyScroll(double x, double y);
}
```

The scroll space is host-defined. The pipeline uses `scroll − contentOffset` and the scrollable sizes to clamp a drag. A platform that reports no native ceiling signals the pipeline not to clamp.

## IMinimapInputHost

```csharp
public interface IMinimapInputHost
{
    (double X, double Y) PointerPosition { get; }
    bool IsPressed { get; }
    bool IsCaptured { get; }
    WorkflowBounds ClampRect { get; }
    bool Capture();
    void Release();
}
```

| Member | Meaning |
|---|---|
| `PointerPosition` | Overlay-local pointer position. |
| `IsPressed` | Whether the primary button is down. |
| `IsCaptured` | Whether the platform captured the pointer. |
| `ClampRect` | Optional hit rectangle; when empty, the pipeline uses its own placed rectangle. |
| `Capture()` | Captures the pointer; returns whether capture succeeded. |
| `Release()` | Releases capture. |

## MinimapMetrics

```csharp
public readonly struct MinimapMetrics : IEquatable<MinimapMetrics>
```

| Member | Type | Default | Meaning |
|---|---|---:|---|
| `Width` | `double` | `200d` | Requested width before clamping. |
| `Height` | `double` | `140d` | Requested height before clamping. |
| `Available` | `SurfaceAvailableArea` | margin 12 | The free corner. |
| `MinSize` | `double` | `20d` | Smallest width or height. |
| `Padding` | `double` | `2d` | Inner padding around the mapped content. |
| `NodeCornerRadius` | `double` | `1d` | Thumbnail corner radius. |
| `MinimapCornerRadius` | `double` | `4d` | Frame corner radius. |
| `MinimumThumbSize` | `double` | `2d` | Smallest rendered thumbnail edge. |
| `Default` | `static MinimapMetrics` | — | The values above. |

`Equals(MinimapMetrics)` compares every placement input, so an unchanged metrics object does not cause a remap.

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
{
    public double Right { get; init; }
    public double Top { get; init; }
    public double Bottom { get; init; }
    public double Margin { get; init; }
    public bool IsUsable { get; }
    public WorkflowBounds GetRect(double desiredWidth, double desiredHeight, double minimumSize);
    public bool Equals(SurfaceAvailableArea other);
}
```

`GetRect` places the requested box at the top-right of the corner, clamps it to the free area and `max(1, minimumSize)`, and falls back to `(0,0)` when the area is unusable. The full description, including `SurfaceMetrics.Available`, is on [Surface math](../../07_canvas-input-navigation/03_surface-math/index.md).

## Notes

- `IWorkflowMinimapOverlay` is the only member of this group the surface behavior writes. The other interfaces are implemented by the adapter's pipeline.
- `MinimapMetrics` is a value type; assign a new value rather than mutating a copy.
- `MinimumThumbSize` prevents a far-away node from disappearing entirely.
