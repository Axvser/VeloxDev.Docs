# API — Attached Behaviors · Adapter-Specific Overlays & Hosts

Beyond the shared behavior set, some adapters ship additional workflow view types that replace or extend a piece of the common surface.

## Class: `WorkflowLinkOverlay` (MAUI)

MAUI renders workflow links as a dedicated graphics layer rather than per-link visuals. `Src/Adapters/VeloxDev.MAUI/Attached/Workflow/WorkflowLinkOverlay.cs`.

```csharp
public sealed class WorkflowLinkOverlay : GraphicsView
```

Bindable properties / CLR properties:

| Property | Type | Description |
|---|---|---|
| `WorkflowTree` | `IWorkflowTreeViewModel?` | Tree whose links are drawn. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Scroll offsets (fed by the surface). |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Canvas content offset. |
| `RulerThickness` | `double` | Ruler band inset to skip when drawing. |
| `LinkLineColor` | `Color?` | Solid link stroke. |
| `VirtualLineColor` | `Color?` | Stroke used for virtual/out-of-reach link segments. |
| `StrokeWidth` | `double` | Link stroke width. |

The overlay draws link polylines with the MAUI graphics `IDrawable` model (`Draw(ICanvas canvas, RectF dirtyRect)`), including arrowheads. It is the MAUI forwarding surface for the link visuals that the XAML adapters attach to individual link views. *Exact drag/reroute semantics `*inferred*` — not exercised by an automated demo.*

## Class: `WorkflowGridDecorator` (Jalium)

Jalium ships a ready-made grid/ruler decorator element (WPF/Avalonia/WinUI instead get it from the `*-v-decorator` templates). `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowGridDecorator.cs`.

```csharp
public class WorkflowGridDecorator : Decorator, IWorkflowGridDecorator
```

Dependency properties:

| Property | Type | Notes |
|---|---|---|
| `RulerThickness` | `double` | Ruler band thickness. |
| `GridSpacing` | `double` | Minor grid spacing. |
| `MajorLineEvery` | `int` | Every N-th minor line is major. |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | The `IWorkflowGridDecorator` offsets. |

It also exposes `RulerBand => RulerThickness` (the interface's read-only band thickness, used for virtualization inset).

## Class: `WorkflowTreeView` (Jalium)

A ready-made composite host control for the whole workflow editor. `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowTreeView.cs`.

```csharp
public class WorkflowTreeView : Grid
```

| Member | Type | Description |
|---|---|---|
| `PART_SurfaceBorder` | `Border` (get) | Surface border. |
| `PART_ScrollViewer` | `ScrollViewer` (get) | Inner scroll viewer (auto scrollbars, transparent background). |
| `PART_Canvas` | `Canvas` (get) | Node/link canvas. |
| `PART_GridDecorator` | `FrameworkElement` (get) | The active grid decorator. |
| `PART_MinimapOverlay` | `FrameworkElement?` (get) | The active minimap overlay. |
| `TemplateSelector` | `IWorkflowTemplateSelector?` | Factory for node/link views; set before assigning `ViewModel`. |
| `ViewModel` | `IWorkflowTreeViewModel?` | The workflow tree; setting it also sets `DataContext`. |
| `GridDecorator` (set) | `IWorkflowGridDecorator?` | Swaps in a styled grid decorator. |
| `MinimapOverlay` (set) | `IWorkflowMinimapOverlay?` | Adds a styled minimap overlay. |

It also hosts the surface behavior: internal wiring applies `WorkflowSurfaceBehavior` over the named `PART_*` parts so panning, zoom, and viewport feed work from one control.

## Interface: `IWorkflowTemplateSelector` (WinForms / Jalium)

The attached-behaviors namespace's template-selector factory (WinForms: `Src/Adapters/VeloxDev.WinForms/Attached/Workflow/ViewManager.cs`; Jalium: `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/IWorkflowTemplateSelector.cs`).

| Adapter | Member |
|---|---|
| WinForms | `Control CreateView(object item)` |
| Jalium | `FrameworkElement CreateView(object item)` |

## Razor component helpers

Razor ships two small static helpers alongside the component behaviors, both in `VeloxDev.WorkflowSystem.AttachedBehaviors`:

### `WorkflowGeometryScope`

Suppresses per-node geometry writes during a zoom transaction so the atomic `applyZoomSurface` browser frame is the only geometry authority for the gesture.

| Member | Signature | Description |
|---|---|---|
| `IsZooming` | `static bool` | True while a zoom transaction is active on the current async flow. |
| `Zoom()` | `static IDisposable` | Enters a transaction; dispose the returned handle to leave it. |

Uses `AsyncLocal<int>` (never a plain static flag) so Blazor Server circuits sharing the process cannot observe each other's zoom.

### `WorkflowRuntimeIds`

Assigns stable, process-lifetime unique ids to workflow components by reference (weakly held), so Blazor elements can carry a `data-*-id` attribute that round-trips through JavaScript and resolves back to the same object.

| Member | Signature | Description |
|---|---|---|
| `Get` | `static string Get(object component)` | Stable id, assigning one on first use. |
| `TryFind` | `static bool TryFind<T>(string? id, out T? value) where T : class` | Resolves a component back from a previously assigned id. |
| `Enumerate` | `static IEnumerable<KeyValuePair<object, string>> Enumerate()` | All registered ids (diagnostics/tests). |
