# Run and Verify

Run the Windows target and exercise each interaction below.

## Run

```powershell
dotnet run
```

**Expected result:** an unpackaged WinUI window opens with three node cards and one link; the minimap is over the surface's top-right corner.

## What to check

1. **Drag a card.** The node moves; the link follows the measured slot anchors.
2. **Press one port, release on another.** A link is created; releasing on empty canvas cancels.
3. **Ctrl+wheel.** The pointer stays over the same world point while the canvas scales; `Scale` clamps to `[0.1, 10]`.
4. **Zoom to about 40%.** Links must still meet their ports. This is the check the offset frame exists for; a link that vanishes or detaches at deep zoom is a clipping bug, not a data bug.
5. **Ctrl+Z / Ctrl+Y.** Structural changes undo and redo.
6. **Shift+wheel.** The surface scrolls sideways.
7. **Right-click a link.** The native flyout's `Delete` entry removes that link.

**Expected result:** no link detaches, no link disappears at deep zoom, and the minimap tracks the scroll.

## If the canvas is blank

The surface resolves `PART_*` through the `UserControl`'s name scope. A code-built surface must register the names and call `WorkflowSurfaceBehavior.Refresh(host)`; a missing `Refresh` after a host or template change leaves the old resolution in place. WinUI's surface is the adapter that exposes `Refresh` for exactly this reason.

**Expected result:** after `Refresh`, the canvas transform and the grid decorator receive the same content offset, and the node pool starts materializing views.
