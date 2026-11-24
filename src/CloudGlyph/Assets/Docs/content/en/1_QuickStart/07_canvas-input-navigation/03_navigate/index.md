# Navigation

Navigation has two halves. The **gestures** move the surface: left-drag on blank canvas pans, `Ctrl` + wheel zooms, and the scroll container carries both. The **capabilities** move the surface to a target: `IWorkflowSurfaceNavigator.CenterOn` and the `Locate()` extensions. Both are optional registrations an attached adapter supplies, so a host can call them without knowing the platform.

## Built-in gestures

| Gesture | What happens | Where it is implemented |
|---|---|---|
| Left-drag on blank canvas | Pans by writing the scroll offsets. A press that a subscriber prevents does not start a pan. | `WorkflowSurfaceBehavior` |
| `Ctrl` + wheel | Zooms around the viewport centre. One notch multiplies `Layout.Scale` by `1/1.1` (wheel up) or `1.1` (wheel down), clamped to `0.1`–`10`. | `WorkflowSurfaceBehavior` with `ZoomEnabled="True"` |
| Plain wheel | Vertical scroll, using the platform's own step. On WPF one notch is `WheelScrollLines × 16` px (48 px at the default 3 lines). | `WorkflowSurfaceBehavior` |
| Wheel over a sibling control | Does not scroll the canvas. | `WorkflowSurfaceBehavior` |

The zoom pivot is the world point under the viewport centre. The adapter captures that point, changes the scale, extends the canvas cover if the zoom pulls content across the origin, then scrolls so the captured point stays under the centre. Node geometry does not move during the zoom; only the scroll does.

## Locate a component

`WorkflowNavigationEx` adds `Locate()` to nodes, slots and links. It converts the element to a canvas-local point from **model data**, then asks the navigator to centre that point:

| Target | Point used |
|---|---|
| `INodeComponent` | The node rectangle's centre. |
| `ISlotComponent` | The parent node's rectangle centre. A slot's own `Anchor` is not read. |
| `ILinkComponent` | The midpoint between the two endpoint nodes' rectangle centres. The published curve is not read. |

Because nothing measured or drawn is involved, an off-screen node or an unmeasured slot can be located before it has a view. The calls return `false` and change nothing when no surface navigator is attached or the target has no finite position.

```csharp
using VeloxDev.WorkflowSystem.StandardEx;

// Pan only: the current zoom is preserved.
bool moved = node.Locate();
bool slotMoved = slot.Locate();
bool linkMoved = link.Locate();
```

If the target cannot be centred inside the current scrollable extent, the WPF surface grows the canvas by the missing amount, then re-centres. WinForms, whose pan engine accepts signed targets, has no extent ceiling.

## The two capabilities

An attached adapter registers both objects on the tree's route:

```csharp
var input = WorkflowInput.For(tree);

// Turn a wheel delta into this platform's scroll.
input.Scroller?.ScrollBy(wheelDeltaX, wheelDeltaY);

// Put a canvas-local point at the viewport centre.
input.Navigator?.CenterOn(localX, localY);
```

Both are `null` until an adapter registers them, and both are cleared when it detaches. A host treats them as optional.

`SurfaceScrollerCore` is the Core implementation of both interfaces. An adapter supplies a narrow `ISurfaceScrollHost` — offsets, extents, viewport size, a wheel profile, an `ApplyOffset` and an `ExpandCanvas` — and the arithmetic is written once:

- A zero delta on one axis leaves that axis alone.
- The horizontal positive is "right", the vertical positive is "away from the user"; they are not the same physical direction, so `ScrollBy` subtracts on the vertical axis and a caller mapping one axis to the other flips the sign itself.
- Overscroll grows the canvas by `WorkflowSurfaceMath.DefaultPanExtendRatio` (`0.15`) instead of stopping at the edge; the maximum is re-read after the host adopts the new extent.
- `CenterOn` uses `WorkflowSurfaceMath.CenterScroll`, and grows the canvas by the exact excess when the target cannot be centred.

## Expected result

- Left-dragging blank canvas moves all nodes and links together; the status-bar zoom text stays unchanged.
- `Ctrl` + wheel changes the zoom around the point under the viewport centre, not around the world origin.
- Calling `node.Locate()` scrolls that node to the centre at the current zoom.
- Calling `Locate()` on a node far outside the current extent grows the canvas and still centres it.

## Next

[Verification](../04_verification/index.md) runs the behaviours end to end and holds the complete code.
