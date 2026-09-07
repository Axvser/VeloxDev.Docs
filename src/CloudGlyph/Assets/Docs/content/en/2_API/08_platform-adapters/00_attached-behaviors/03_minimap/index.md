# API — Attached Behaviors · Minimap Overlay

`WorkflowMinimapOverlay` renders a thumbnail of all nodes/links plus a draggable viewport indicator, so the user can see and navigate the whole workflow. It implements the Core data-exchange contract `IWorkflowMinimapOverlay` (and therefore `IWorkflowGridDecorator`).

## Class: `WorkflowMinimapOverlay`

| Adapter | Declared as | Drawing model |
|---|---|---|
| WPF | `public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay` | OnRender geometry |
| Avalonia | `public class WorkflowMinimapOverlay : Control, IWorkflowMinimapOverlay` | Control render (StyledProperties) |
| WinUI | `public class WorkflowMinimapOverlay : Canvas, IWorkflowMinimapOverlay` | XAML `Rectangle` / `Line` shapes |
| MAUI | `public class WorkflowMinimapOverlay : GraphicsView, IDrawable, IWorkflowMinimapOverlay` | `IDrawable.Draw(ICanvas, RectF)` |
| WinForms | `public static class WorkflowMinimapOverlay` | paints the registered control's surface |
| Jalium | `public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay` | OnRender geometry |
| Razor | `partial class WorkflowMinimapOverlay : ComponentBase, IWorkflowMinimapOverlay, IAsyncDisposable` | SVG/DOM via JS interop |

### Shared property surface (WPF / Avalonia / WinUI / MAUI / Jalium)

Beyond the interface members the overlay exposes styling/geometry properties. WPF example (same names on the others; `Brush` ↔ `IBrush`/`Color` per platform):

| Property | Type | Default (WPF) |
|---|---|---|
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` |
| `RulerThickness` | `double` | `28` |
| `LinkStrokeThickness` | `double` | `2` |
| `MinimapBackground` / `MinimapBorderBrush` | brush | dark blue-grey / border |
| `NodeBrush` / `LinkBrush` | brush | sky blue / soft grey |
| `ViewportStroke` / `ViewportFill` / `ViewportStrokeThickness` | brush / brush / `double` | white stroke, translucent fill |
| `MinimapCornerRadius` / `MinimapBorderThickness` / `NodeCornerRadius` | `double` | `4` / `1` / `1` |
| `ContentPadding` / `MinimapMinSize` | `double` | `2` / `20` |
| `ScrollViewerName` | `string?` | `null` (resolved on load for drag-to-navigate) |
| `RulerBand` (get-only, on the interface) | `double` | `0` for the minimap itself |

MAUI uses color-typed bindable properties instead of brushes (`MinimapBackgroundColor`, `MinimapBorderColor`, `NodeFillColor`, `LinkStrokeColor`, `ViewportStrokeColor`, `ViewportFillColor`, …), and Avalonia uses `IBrush` `StyledProperty`s with an extra `MinimapMargin`. *Per-adapter defaults are source-verified; visual parity across adapters is `*inferred*`.*

### Behavior (verified, WPF)

- Subscribes to the tree's node/link collections for dirty tracking and re-measures the world bounds.
- **Viewport drag:** pressing inside the viewport rect keeps it in place and aligns it to the cursor; pressing elsewhere moves the viewport block center to the cursor, clamped inside the minimap.
- **Navigate-to-world:** converts minimap space back to world coordinates and scrolls the `ScrollViewer`, growing `Layout.NegativeOffset` / `PositiveOffset` at the edges.
- Surface behavior pushes `ScrollOffset*`, `ContentOffset*`, `ViewportWidth/Height`, `WorkflowTree`, and `IsMinimapVisible` before each render pass.

## Interface: `IWorkflowGridDecorator`

Data-exchange contract for the grid decorator; the surface behavior pushes the scroll offsets and the canvas content offset into it before each render pass. **Defined in Core** (`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowGridDecorator.cs`, namespace `VeloxDev.WorkflowSystem`), shared by all seven adapters.

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

`RulerBand` is the thickness of the floating ruler/scale band the decorator draws over the TOP/LEFT canvas edges; the adapter surfaces read it and forward it to `WorkflowSpatialEx.SetVirtualizeInset` so spatial virtualization does not cull nodes under the band.

## Interface: `IWorkflowMinimapOverlay`

Derives from `IWorkflowGridDecorator` (the minimap also needs the scroll/content offsets) and adds the viewport size and the tree to render. **Defined in Core** (`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowMinimapOverlay.cs`, namespace `VeloxDev.WorkflowSystem`).

```csharp
public interface IWorkflowMinimapOverlay : IWorkflowGridDecorator
{
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    IWorkflowTreeViewModel? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
}
```

## WinForms static overlay

`WorkflowMinimapOverlay` on WinForms is a static attached-style holder: `SetIsEnabled(Control, bool)` / `SetWorkflowTree(Control, IWorkflowTreeViewModel?)` and matching getters. The behavior registers paint handling on the control; the actual thumbnail is drawn into the control's `Paint` surface. *Detail inferred from source — no automated demo draws it.*

## Razor component

`WorkflowMinimapOverlay.razor` + code-behind implement `IWorkflowMinimapOverlay` with parameters `Width` (180), `Height` (120), `Background`, `BorderColor`, `NodeFill`, `NodeRadius`, `ViewportFill`, `ViewportStroke`, `ViewportStrokeWidth`, `Padding`, `ScrollViewerId`, plus the six interface offset/viewport members. Drag navigation resolves through the scroll `id` and updates `ScrollOffset*`.
