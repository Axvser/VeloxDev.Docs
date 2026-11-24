# Run and Verify

The editor is verified by exercising the six things the surface owns: render, drag, connect, pan, zoom and input routing.

## Run

```powershell
dotnet run
```

**Expected result:** a window opens with three node cards and one link. The minimap is in the top-right corner of the surface.

## What to check

1. **Drag a node's card.** The node follows the pointer and the link's endpoints follow once the slot layout writes the new anchors.
2. **Press one port and release on another.** A link is created. Releasing on empty canvas cancels the preview.
3. **Ctrl+wheel.** The point under the pointer stays under it while the canvas scales. The gesture clamps to `[0.1, 10]`.
4. **Zoom to about 40%.** Links must still meet their ports; almost every link bug is invisible at 100%.
5. **Ctrl+Z / Ctrl+Y.** Structural changes undo and redo. A completed drag is not in the history.
6. **Shift+wheel.** The surface scrolls sideways. A plain wheel scrolls vertically.
7. **Right-click a link.** The `Delete` entry removes it.

**Expected result:** each step leaves the surface consistent; no link detaches, and the minimap's viewport block tracks the scroll.
