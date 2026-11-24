# Run and Verify

Run the Windows target and exercise each interaction below.

## Run

```powershell
dotnet build -t:Run -f net10.0-windows10.0.19041.0
```

**Expected result:** the packaged Windows MAUI application starts and shows three node cards with one link, plus the minimap over the surface's top-right corner.

## What to check

1. **Drag a card.** The node moves; the link follows the measured slot anchors.
2. **Press one port, release on another.** A link is created; releasing on empty canvas cancels.
3. **Ctrl+wheel.** The pointer stays over the same world point while the canvas scales.
4. **Zoom to about 40%.** Links must still meet their ports. The overlay is viewport-sized precisely so it survives deep zoom; a layer that vanishes is the Win2D texture cap.
5. **Hover a link and press Delete.** The link is removed. If hovering does nothing, check `InteractionSource`.
6. **Shift+wheel.** The surface scrolls horizontally.
7. **Right-click a link.** The `Delete` entry removes that link.
8. **Click the minimap.** The viewport recentres on the pressed point.

**Expected result:** the surface stays consistent at every step and the overlay's links stay attached at deep zoom.
