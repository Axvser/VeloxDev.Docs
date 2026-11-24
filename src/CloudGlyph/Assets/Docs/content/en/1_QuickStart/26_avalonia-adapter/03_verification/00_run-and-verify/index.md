# Run and Verify

Run the desktop target and exercise each interaction below.

## Run

```powershell
dotnet run
```

**Expected result:** a desktop window opens with three node cards and one link; the minimap sits over the surface's top-right corner.

## What to check

1. **Drag a card.** The node moves and the link follows the measured slot anchors.
2. **Press one port, release on another.** A link is created; releasing on empty canvas cancels.
3. **Ctrl+wheel.** The point under the pointer stays put; the adapter clamps `Scale` to `[0.1, 10]`.
4. **Zoom to about 40%.** Links must still meet their ports.
5. **Ctrl+Z / Ctrl+Y.** Structural changes undo and redo; a drag is not in the history.
6. **Shift+wheel.** The surface scrolls horizontally.
7. **Right-click a link.** The `Delete` entry removes that link.

**Expected result:** the surface stays consistent at every step; no link detaches and the minimap tracks the scroll.
