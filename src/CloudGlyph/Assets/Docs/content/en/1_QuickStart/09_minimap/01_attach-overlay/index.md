# Attach the overlay

The minimap is an overlay, not a child of the scroll viewer. It spans the surface, draws itself in the free corner, and receives its data from the surface behavior, which finds it by name.

## Markup

```xml
<Grid>
    <Border x:Name="PART_SurfaceBorder">
        <local:WorkflowGridDecorator x:Name="PART_GridDecorator">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}" />
            </ScrollViewer>
        </local:WorkflowGridDecorator>
    </Border>

    <!-- Full-surface layer. The overlay itself draws only the 200 x 140 corner. -->
    <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                      HorizontalAlignment="Stretch"
                                      VerticalAlignment="Stretch"
                                      ScrollViewerName="PART_ScrollViewer" />
</Grid>
```

On the host `UserControl`:

```xml
behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
```

`MinimapOverlayName` is what makes the surface push data; without it the overlay has no tree and draws nothing. `ScrollViewerName` on the overlay itself is what lets a drag write scroll offsets back.

The names are resolved in the `UserControl` namescope. The overlay must be inside the same `UserControl` as the surface, not in a sibling window or another control's resource dictionary.

## What the surface pushes

Once per layout/scroll pass, `SurfaceMetricsPush.PushMinimap` writes:

| Property | Source |
|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | The scroll viewer's offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`. |
| `ViewportWidth` / `ViewportHeight` | The scroll viewer's viewport. |
| `WorkflowTree` | The surface's `DataContext`. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | The free corner: width minus the vertical scrollbar, top at the ruler band, bottom above the horizontal scrollbar. |
| `MinimapMargin` | The gap the overlay keeps from that corner. |

The subtraction lives in `SurfaceMetrics.Create`, so every adapter shrinks the corner the same way. If the grid decorator reports a `RulerBand`, the minimap starts below it.

## Placement

`MinimapPipelineCore.MinimapRect` places the requested `MinimapWidth` × `MinimapHeight` at the top-right of the available corner, clamping to the free area and `MinimapMinSize`. Defaults are 200 × 140, 20 minimum, 12 margin.

If the surface's named parts appear after the overlay is loaded, call `WorkflowSurfaceBehavior.Refresh(host)` so the resolved minimap is pushed again.

## Expected result

- The minimap appears in the top-right corner of the canvas, above the scrollbars.
- It shows one thumbnail per visible or off-screen node and a rectangle for the current viewport.
- Scrolling the canvas moves the viewport rectangle inside the minimap.
- Without `MinimapOverlayName` the overlay stays blank; without `ScrollViewerName` dragging the minimap cannot scroll the surface.

## Next

[Appearance and navigation](../02_appearance-navigation/index.md) covers sizing, styling, visibility and drag.
