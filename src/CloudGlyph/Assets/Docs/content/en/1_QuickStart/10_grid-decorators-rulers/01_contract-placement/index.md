# Contract and placement

The surface behavior does not know how a grid is drawn. It knows one interface and one name: the element named by `GridDecoratorName` must implement `IWorkflowGridDecorator`, and the behavior pushes the current offsets into it.

## The contract

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double RulerBand { get; }
}
```

| Member | Meaning |
|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | The surface `ScrollViewer`'s offsets, in scroll space. |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`, the canvas's own translation. |
| `RulerBand` | Thickness of the floating band that overlaps the top and left content edges; `0` when there is no band. |

The offsets are written by `SurfaceMetricsPush.PushGrid` on every scroll, pan and zoom. The decorator does not subscribe to anything; it invalidates its visual when a property changes.

## Placement

The decorator is the **parent** of the scroll viewer:

```xml
<Border x:Name="PART_SurfaceBorder">
    <local:GridRulerDecorator x:Name="PART_GridDecorator">
        <ScrollViewer x:Name="PART_ScrollViewer"
                      HorizontalScrollBarVisibility="Auto"
                      VerticalScrollBarVisibility="Auto">
            <Canvas x:Name="PART_Canvas"
                    Width="{Binding Layout.ActualSize.Width}"
                    Height="{Binding Layout.ActualSize.Height}">
                <Canvas.RenderTransform>
                    <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                        Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                </Canvas.RenderTransform>
            </Canvas>
        </ScrollViewer>
    </local:GridRulerDecorator>
</Border>
```

with the host attached property:

```xml
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
```

Two placement rules matter:

1. **The decorator wraps the content; it is not inside the canvas.** It must paint at viewport size and see the scroll offsets, which only the host above the `ScrollViewer` can do.
2. **The canvas is translated by `RulerThickness`.** The world origin then sits at the inner edge of the ruler band, while content can still scroll under the translucent band. If the canvas is not translated, the band covers the first rows/columns of the world.

## What the surface pushes

`SurfaceMetricsPush.PushGrid` writes the four offsets, then calls:

```csharp
tree.SetVirtualizeInset(left: decorator.RulerBand, top: decorator.RulerBand);
```

The inset inflates the virtualization query without moving the authoritative `Viewport`. A node that is visually under the ruler but inside the viewport is therefore kept. The minimap reads the same value as `AvailableTop`, so it starts below the band instead of overlapping it.

`RulerBand` is read-only on the interface: it is a function of the decorator's own configuration, not something the surface writes.

## Expected result

- The grid lines move with the content and stay aligned with the scrollbars.
- The rulers stay fixed at the top and left edges while the content scrolls beneath them.
- A node dragged under the ruler band is not removed from the visible set while it is still inside the viewport.
- The minimap's top edge sits below the ruler band, not over it.

## Next

[Draw grid and rulers](../02_draw-grid-rulers/index.md) covers the drawing pass and the four formulas.
