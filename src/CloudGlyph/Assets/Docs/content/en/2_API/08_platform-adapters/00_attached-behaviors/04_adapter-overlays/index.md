# API — Attached Behaviors · Adapter-Specific Overlays & Hosts

Beyond the shared behavior set, some adapters ship additional workflow view types that replace or extend a piece of the common surface.

## Class: `WorkflowLinkOverlay` (MAUI)

MAUI draws, in one viewport-sized `GraphicsView`, the links that have **no view of their own** — the immediate-mode hosts and the frames before a pooled link view has materialized. A link that published its curve together with the control that drew it is painted by that control and skipped here. `Src/Adapters/VeloxDev.MAUI/Attached/Workflow/WorkflowLinkOverlay.cs`.

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
| `LinkFlowEnabled` | `bool` | Toggles the travelling-light animation along each curve. |
| `InteractionSource` | `View?` | The view already on the surface's input path that forwards hover/press to the hit test (the overlay itself stays `InputTransparent`). |

The overlay draws each link as one cubic Bézier with the MAUI graphics `IDrawable` model (`Draw(ICanvas canvas, RectF dirtyRect)`); the travelling light is cut out of that curve by arc length rather than mapped along a polyline. It is paint-only (`VisualElement.InputTransparent` stays `true`, so a viewport-sized view cannot swallow the canvas gestures); interaction is driven through `InteractionSource` — the hit test tracks which link the pointer is on, `Delete` removes it, and a right press (or, off Windows, a long press) is forwarded to `LinkInteraction` so the host surface can open its own menu.

**Hover feedback is the host's**, and this layer paints resting links only. A host that wants a hovered link to look different subscribes the tree's `IInputEvents` and draws its own layer above this one, from the curve the link published (`ILinkHitTestable.Curve`) — so the two can never disagree about where the line is. *Exact drag/reroute semantics `*inferred*` — not exercised by an automated demo.*

## Class: `WorkflowGridDecorator` (Jalium)

Jalium ships a ready-made grid/ruler decorator, as do WinForms (`.cs`) and Razor (`.razor`); WPF/Avalonia/WinUI instead get one from the `*-v-decorator` template. `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowGridDecorator.cs` is a plain drawing/configuration class (no base type and **no** `IWorkflowGridDecorator` implementation); the composite `WorkflowTreeView` owns it through its `GridDecorator` property.

```csharp
public class WorkflowGridDecorator
```

| Member | Type | Notes |
|---|---|---|
| `RulerThickness` | `const double` (36) | Ruler band thickness. |
| `MinorGridColor` / `MajorGridColor` / `AxisColor` | `Color` | Grid palette. |
| `RulerBackground` / `RulerLabelColor` / `RulerTickColor` / `RulerDividerColor` | `Color` | Ruler palette. |
| `GridStep` | `double` | Minor grid spacing. |
| `MajorLineEvery` | `int` | Every N-th minor line is major. |
| `MajorStep` | `double` (get) | `GridStep * Math.Max(1, MajorLineEvery)`. |

## Class: `WorkflowTreeView` (Jalium)

The composite host control for the whole workflow editor, and Jalium's entire surface — Jalium ships no standalone `WorkflowSurfaceBehavior`. `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowTreeView.cs`.

```csharp
public class WorkflowTreeView : Canvas
```

| Member | Type | Description |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel?` (get) | The workflow tree currently attached. |
| `PortLayout` | `WorkflowPortLayout` | The design-time port layout shared by the per-role attachments. |
| `GridDecorator` | `WorkflowGridDecorator` | The grid/ruler decorator. |
| `TemplateSelector` | `IWorkflowTemplateSelector?` | Factory for node/link views; set it before `SetTree`. |
| `OriginX` / `OriginY` | `double` (get) | World origin plus the ruler band. |
| `ContentOriginX` / `ContentOriginY` | `double` (get) | The world origin (`Layout.ActualOffset`). |
| `AttachScrollViewer(ScrollViewer)` | method | Wires the scroll viewer that drives panning. |
| `SetTree(IWorkflowTreeViewModel?)` | method | Attaches a tree and hooks the view pool. |
| `NotifyZoomCommitted(hx, vy)` | method | Applies a zoom pivot after the host handled a pinch/wheel. |
| `NavigateToWorld(wx, wy)` | method | Scrolls so a world point is visible. |
| `OnBuildLinkMenu` | `protected virtual void` | Builds the link context menu on each right press; the base adds a single **Delete** item — override to add or remove entries. |

Unlike the other six adapters, Jalium names no `PART_*` controls and applies no static surface behavior: it computes port geometry and positions views from the model rather than measuring visuals, so the tree view itself is the surface.

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
