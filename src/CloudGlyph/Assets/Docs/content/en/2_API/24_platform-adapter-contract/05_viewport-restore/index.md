# Viewport restore

A newly attached surface must open at the tree's saved scroll position, not at the origin. `SurfaceViewportRestoreCore` owns the state machine; an adapter supplies only the platform deferral and the two writes.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## SurfaceViewportRestoreCore

**Signature:** `sealed class SurfaceViewportRestoreCore`

| Member | Type | Description |
| --- | --- | --- |
| `HasPendingRestore` | `bool` | Whether a captured position is still waiting to be restored. |
| `Capture(ITreeComponent? tree)` | `void` | Captures `tree.Layout.ViewportOffset` when the tree differs from the last captured one. A null tree is ignored. |
| `Schedule(ISurfaceViewportRestoreHost host, Action? afterRestore = null)` | `void` | Schedules one deferred restore when a position is pending. Calling it again while queued does nothing. Throws `ArgumentNullException` for a null host. |

Capture is keyed on the tree instance, so repeated refreshes of the same tree never move the user back. `Capture` must run **before** the surface writes its current viewport back to `Layout.ViewportOffset`, or the saved position is overwritten with the origin.

`Schedule` hands the host a callback that:

1. Clears `isQueued`.
2. Returns without consuming the pending position when `host.IsRestoreEnabled` is false, so a later pass retries.
3. Clears the pending position and applies the captured offsets clamped by `host.HorizontalMaximum` / `host.VerticalMaximum`.
4. Runs `afterRestore`.

## ISurfaceViewportRestoreHost

**Signature:** `interface ISurfaceViewportRestoreHost`

| Member | Type | Description |
| --- | --- | --- |
| `IsRestoreEnabled` | `bool` | Whether the surface is still attached and its scroll container resolved. |
| `HorizontalMaximum` / `VerticalMaximum` | `double` | Current scroll limits. |
| `ApplyOffset(double horizontalOffset, double verticalOffset)` | `void` | Writes both offsets. |
| `DeferRestore(Action restore)` | `void` | Schedules the callback after the platform laid out the newly attached tree. |

The adapter decides when layout is complete; everything that decides whether and what to restore stays in Core.

```csharp
var restore = new SurfaceViewportRestoreCore();

// before the surface writes its first viewport
restore.Capture(tree);

// after the named parts are resolved
restore.Schedule(host, afterRestore: () => SurfaceMetricsPush.PushViewport(metrics, tree));
```

**Expected result:** a tree with a non-zero `Layout.ViewportOffset` opens at that offset; a tree without one stays at the origin. A second refresh of the same tree does not move the user.
