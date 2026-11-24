# Link overlay

`WorkflowLinkOverlay` is a single `GraphicsView` that draws every link in the visible set plus the virtual preview, in one viewport-sized layer. It must live outside the growing world canvas: a canvas-sized `GraphicsView` exceeds Win2D's roughly 16k device-pixel texture limit at deep zoom and the whole layer disappears silently.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.MAUI`.

## WorkflowLinkOverlay

**Signature:** `sealed class WorkflowLinkOverlay : GraphicsView`

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree whose links are drawn. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Canvas content offsets. |
| `RulerThickness` | `double` | `0` | Ruler band to avoid. |
| `LinkLineColor` | `Color?` | translucent white | Resting link colour. |
| `VirtualLineColor` | `Color?` | translucent white | Virtual link colour when no stage colour applies. |
| `VirtualValidTargetColor` | `Color?` | `null` | Virtual link colour over a valid receiver; `null` keeps `VirtualLineColor`. |
| `VirtualInvalidTargetColor` | `Color?` | `null` | Virtual link colour over a refusing slot; `null` keeps `VirtualLineColor`. |
| `StrokeWidth` | `double` | `4` | Link stroke width. |
| `LinkFlowEnabled` | `bool` | `false` | Enables the travelling flow highlight. |
| `InteractionSource` | `View?` | `null` | The view whose pointer/keyboard input drives link interaction. |
| `BandCentre` | `double` | runtime | Flow band position as a fraction of the link length. |
| `BandMix` | `double` | runtime | Flow band blend factor. |

The overlay is `InputTransparent = true`; `InteractionSource` is what makes links hoverable and deletable. Set it to a view already on the surface's input path (an ancestor of the canvas), never the overlay itself. Leave it unset and links paint but never answer a pointer.

The overlay draws **resting** links only. A hover highlight is the host's: subscribe the tree's `IInputEvents`, read the curve the link publishes, and draw your own layer above.

```xml
<behaviors:WorkflowLinkOverlay x:Name="PART_LinkLayer"
                               WorkflowTree="{Binding BindingContext, Source={x:Reference Root}}"
                               InteractionSource="{x:Reference Root}"
                               ScrollOffsetX="{Binding ScrollOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ScrollOffsetY="{Binding ScrollOffsetY, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetX="{Binding ContentOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetY="{Binding ContentOffsetY, Source={x:Reference PART_GridDecorator}}"
                               RulerThickness="0" StrokeWidth="2" />
```

**Expected result:** links appear when both slot anchors are measured; hovering the painted body (six units either side) reaches the link, and Delete removes the hovered link through its `DeleteCommand`.
