# Scroll and navigation

The two capabilities an adapter registers on `WorkflowInput` while its surface is attached. Core also ships a ready implementation, `SurfaceScrollerCore`, which an adapter drives through a small platform host.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## IWorkflowSurfaceScroller

**Signature:** `interface IWorkflowSurfaceScroller`

| Member | Signature | Description |
| --- | --- | --- |
| `ScrollBy` | `void ScrollBy(double wheelDeltaX, double wheelDeltaY)` | Scrolls as though the wheel turned by the given deltas. An implementation that cannot grow its surface clamps to the extent; a zero delta leaves that axis alone. |

The deltas are **wheel deltas**, the values `PointerWheelEventArgs` carries, not scroll offsets. A positive X moves towards the content on the right; a positive Y moves towards the content above. A caller that drives the other axis flips the sign itself.

## IWorkflowSurfaceNavigator

**Signature:** `interface IWorkflowSurfaceNavigator`

| Member | Signature | Description |
| --- | --- | --- |
| `CenterOn` | `void CenterOn(double localX, double localY)` | Scrolls so the canvas-local point sits at the viewport centre. |

Coordinates use the same frame as `INodeComponent.Anchor` and `ITreeHelper.Viewport`. `WorkflowNavigationEx` (in `VeloxDev.WorkflowSystem.StandardEx`) produces this point from a node, slot or link. An implementation that cannot grow the surface clamps instead.

## ISurfaceScrollHost

**Signature:** `interface ISurfaceScrollHost`

The platform layer `SurfaceScrollerCore` drives.

| Member | Type | Description |
| --- | --- | --- |
| `Layout` | `CanvasLayout?` | Canvas geometry, or `null` when no tree is bound. |
| `ViewportWidth` / `ViewportHeight` | `double` | Visible viewport size. |
| `HorizontalOffset` / `VerticalOffset` | `double` | Current scroll offsets. |
| `HorizontalMaximum` / `VerticalMaximum` | `double` | Largest offsets the platform reports now. |
| `WheelProfile` | `SurfaceWheelProfile` | How this platform converts a wheel delta into a step. |
| `ApplyOffset(double? horizontalOffset, double? verticalOffset)` | `void` | Writes offsets; `null` leaves that axis untouched. |
| `ExpandCanvas()` | `void` | Lets the platform adopt a canvas the scroller grew. |

## SurfaceScrollerCore

**Signature:** `sealed class SurfaceScrollerCore : IWorkflowSurfaceScroller, IWorkflowSurfaceNavigator`

| Member | Type | Description |
| --- | --- | --- |
| `DefaultWheelDelta` | `const double` (`120`) | Wheel delta one physical notch reports on a Win32-based platform. |
| `DefaultLineHeight` | `const double` (`16`) | Line height used when scrolling by lines. |
| `SurfaceScrollerCore(ISurfaceScrollHost host)` | constructor | Throws `ArgumentNullException` for a null host. |
| `ScrollBy(double, double)` | `void` | Converts the wheel delta through `host.WheelProfile`; overshoot past an edge grows the canvas through `WorkflowSurfaceMath.ClampScrollOffset`. |
| `CenterOn(double, double)` | `void` | Places the point at the viewport centre through `WorkflowSurfaceMath.CenterScroll`. |

## SurfaceWheelProfile

**Signature:** `readonly struct SurfaceWheelProfile`

| Member | Type | Description |
| --- | --- | --- |
| `DeltaPerNotch` | `double` (init) | Raw wheel delta for one notch. |
| `PixelsPerNotch` | `double` (init) | Pixels one notch scrolls. |
| `ScrollLines` | `double` (init) | Lines one notch scrolls. |
| `LineHeight` | `double` (init) | Pixels per line. |
| `FromLines(double deltaPerNotch, double scrollLines, double lineHeight = SurfaceScrollerCore.DefaultLineHeight)` | `static SurfaceWheelProfile` | Builds a line-based profile; non-positive `scrollLines` means page scrolling. |
| `FromPixels(double deltaPerNotch, double pixelsPerNotch)` | `static SurfaceWheelProfile` | Builds a pixel-based profile. |

```csharp
var scroller = new SurfaceScrollerCore(myHost);
input.Scroller = scroller;
input.Navigator = scroller;

scroller.ScrollBy(0d, -120d);   // one notch towards the content above
scroller.CenterOn(240d, 160d);  // put that canvas point at the viewport centre
```

**Expected result:** both capabilities are the same object; after `ScrollBy`, the host's offsets and `tree.GetHelper().Viewport` move together on the next surface pass.
