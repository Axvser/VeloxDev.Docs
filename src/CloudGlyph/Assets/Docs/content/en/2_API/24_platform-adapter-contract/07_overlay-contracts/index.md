# Overlay contracts

Two data-exchange interfaces let the surface push the same numbers into a grid decorator and a minimap without knowing how either draws. The XAML adapters do not ship a decorator; the host writes one against this interface, or generates one from the item templates.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## IWorkflowGridDecorator

**Signature:** `interface IWorkflowGridDecorator`

| Member | Type | Description |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` (get/set) | The surface scroll container's offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` (get/set) | The canvas content offsets. |
| `RulerBand` | `double` (get) | Thickness of a floating ruler band overlapping the top/left edges; `0` when none. |

The surface writes the four offsets before each pass. `RulerBand` is read each pass and forwarded to `ITreeComponent.SetVirtualizeInset(left: RulerBand, top: RulerBand)` so nodes under a floating ruler are not culled.

## IWorkflowMinimapOverlay

**Signature:** `interface IWorkflowMinimapOverlay : IWorkflowGridDecorator`

| Member | Type | Description |
| --- | --- | --- |
| `ViewportWidth` / `ViewportHeight` | `double` (get/set) | Viewport size in the same scroll space as the pushed offsets. |
| `WorkflowTree` | `ITreeComponent?` (get/set) | The tree whose nodes and links the minimap renders. |
| `IsMinimapVisible` | `bool` (get/set) | Whether the overlay should render. |
| `AvailableRight` | `double` (get/set) | Right edge of the content viewport in local pixels, excluding the vertical scrollbar. |
| `AvailableTop` | `double` (get/set) | Top edge, below the horizontal ruler band. |
| `AvailableBottom` | `double` (get/set) | Bottom edge, above the horizontal scrollbar. |
| `MinimapMargin` | `double` (get/set) | Gap between the minimap and the available corner. |

The surface pushes all members before each pass through `SurfaceMetricsPush.PushMinimap`. The minimap draws thumbnails and a viewport frame, and resolves a drag back into scroll offsets.

```csharp
public sealed class GridDecorator : Grid, IWorkflowGridDecorator
{
    public double ScrollOffsetX { get; set; }
    public double ScrollOffsetY { get; set; }
    public double ContentOffsetX { get; set; }
    public double ContentOffsetY { get; set; }
    public double RulerBand => 0d;
}
```

**Expected result:** after a scroll, the decorator's `ScrollOffsetX` and `tree.GetHelper().Viewport.Horizontal` move together; a decorator that covers the top/left must return that thickness from `RulerBand`.
