# Viewport state

The surface passes its current state to overlays as an immutable record, and restores a saved scroll position once the layout has settled. Both are Core types so every adapter feeds its overlay the same packet.

## SurfaceViewport

```csharp
public sealed record SurfaceViewport(
    ITreeComponent Tree,
    double ScrollLeft,
    double ScrollTop,
    double ViewportWidth,
    double ViewportHeight,
    double ContentOffsetX,
    double ContentOffsetY);
```

A positional record, so it also gets `Deconstruct`, value equality, and `ToString`. It mirrors exactly what `IWorkflowGridDecorator` and `IWorkflowMinimapOverlay` receive.

## SurfaceCanvas

```csharp
public sealed record SurfaceCanvas(double Width, double Height);
```

The computed canvas size passed to a surface's content fragment, so a child layer can size itself to the same canvas.

## SurfaceViewportFeed

```csharp
public sealed class SurfaceViewportFeed
{
    public SurfaceViewport? Current { get; private set; }
    public event Action<SurfaceViewport>? Changed;
    public void Publish(SurfaceViewport viewport);
}
```

| Member | Description |
|---|---|
| `Current` | Last published snapshot; `null` until the first publish. |
| `Changed` | Raised with the new snapshot on every `Publish`. |
| `Publish` | Stores the snapshot and raises `Changed`. |

A feed lets an overlay subscribe to viewport changes without re-reading the surface or forcing a full render. The Razor surface exposes it as a cascading parameter; other adapters push the same values through `SurfaceMetricsPush`.

## ISurfaceViewportRestoreHost

```csharp
public interface ISurfaceViewportRestoreHost
{
    bool IsRestoreEnabled { get; }
    double HorizontalMaximum { get; }
    double VerticalMaximum { get; }
    void ApplyOffset(double horizontalOffset, double verticalOffset);
    void DeferRestore(Action restore);
}
```

| Member | Description |
|---|---|
| `IsRestoreEnabled` | Host switch; `false` cancels a pending restore. |
| `HorizontalMaximum` / `VerticalMaximum` | Live maxima used to clamp the restored offsets. |
| `ApplyOffset` | Writes the restored offsets. |
| `DeferRestore` | Queues the restore until the host can apply it. |

## SurfaceViewportRestoreCore

```csharp
public sealed class SurfaceViewportRestoreCore
```

| Member | Description |
|---|---|
| `HasPendingRestore` | Whether a restore was captured and not yet applied. |
| `Capture(ITreeComponent? tree)` | Captures the saved viewport once per distinct tree when `HasViewportRestore` is true. Run it before the current viewport is written back. |
| `Schedule(ISurfaceViewportRestoreHost host, Action? afterRestore = null)` | Queues one restore at most; re-checks pending state and the host switch at execution, clamps to the live maxima, then invokes `afterRestore`. Throws `ArgumentNullException` for a null host. |

The sequence is: capture the saved offset during load, let the surface finish its first layout, then schedule. A second `Schedule` before the first runs does not queue a duplicate.
