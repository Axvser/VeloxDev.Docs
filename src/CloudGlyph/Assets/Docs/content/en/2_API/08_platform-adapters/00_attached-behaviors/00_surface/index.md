# API — Attached Behaviors · WorkflowSurfaceBehavior & Canvas Transform

## Class: `WorkflowSurfaceBehavior`

Attached behavior for the workflow surface host — the control that owns the `ScrollViewer` + `Canvas` pair of the editor. It resolves named child controls, feeds the scroll/content offsets to the grid decorator and minimap, starts panning on "blank" surface presses, and hooks the zoom gesture.

Per adapter, the host element type and the property registration differ:

| Adapter | Host element | Declared as | Registration |
|---|---|---|---|
| WPF / WinUI / Jalium | `UserControl` / `FrameworkElement` (Jalium) | `sealed class : DependencyObject` | `DependencyProperty.RegisterAttached` |
| Avalonia | `UserControl` | `sealed class : AvaloniaObject` | `AvaloniaProperty.RegisterAttached<WorkflowSurfaceBehavior, UserControl, T>` |
| MAUI | `ContentView` | `sealed class` | `BindableProperty.CreateAttached` |
| WinForms | `Control` | `sealed class` | private `ConditionalWeakTable<Control, SurfaceState>` |
| Razor | n/a (component) | `partial class WorkflowSurfaceBehavior : ComponentBase, IAsyncDisposable` | parameters |

### Attached property surface (WPF / Avalonia / WinUI / MAUI / Jalium)

Each XAML-style adapter exposes the same attached properties with the usual `Get*` / `Set*` static accessors (property system: `DependencyProperty` on WPF/WinUI/Jalium, `AvaloniaProperty` on Avalonia, `BindableProperty` on MAUI):

| Property | Type | Default | Description |
|---|---|---|---|
| `IsEnabled` | `bool` | `false` | Master switch: hooks `Loaded` / `Unloaded` / `DataContextChanged` and the pointer/scroll events. |
| `ScrollViewerName` | `string?` | `null` | Name of the inner `ScrollViewer` (e.g. `PART_ScrollViewer`). |
| `CanvasName` | `string?` | `null` | Name of the inner `Canvas` (e.g. `PART_Canvas`). |
| `GridDecoratorName` | `string?` | `null` | Name of the element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | Element whose press starts panning (the surface border). |
| `MinimapOverlayName` | `string?` | `null` | Name of the element implementing `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables the framework zoom gesture hook (WPF: `PreviewMouseWheel` on the scroll viewer). |

### Static method: `Refresh(host)`

Re-resolves named controls, re-applies layout, and pushes the visible region to the grid decorator and minimap. Invoked on load, scroll, `DataContextChanged`, and after pan/zoom updates.

| Adapter | Signature |
|---|---|
| WPF / Avalonia / WinUI | `public static void Refresh(UserControl host)` |
| MAUI | `public static void Refresh(ContentView host)` |
| WinForms | `public static void Refresh(Control host)` |
| Jalium | `public static void Refresh(FrameworkElement host)` |

**Jalium extra — `ZoomBy`:**
`public static void ZoomBy(FrameworkElement host, IWorkflowTreeViewModel viewModel, double factor)` — Jalium surfaces zoom as an explicit call (host-driven) instead of a wheel hook.

**WinForms surface also exposes** `SetWorkflowTree(Control element, IWorkflowTreeViewModel? value)` (mirroring the `DataContext` assignment the XAML adapters get for free).

### WinForms state

WinForms has no attached properties; `WorkflowSurfaceBehavior` keeps a private `SurfaceState` per `Control` (via a `ConditionalWeakTable`). The state holds the same flags/names plus the `WorkflowTree`, and installs an `IMessageFilter` so a **Ctrl+wheel zoom gesture is intercepted before any scrollable child** can scroll: it resolves the surface host from the wheel message's target control, applies `tree.Layout.Scale` and zoom-center scroll math, marks the message handled, and swallows it. *Gesture detail is source-verified; not exercised by an automated demo.*

### Razor component

`WorkflowSurfaceBehavior.razor` + code-behind (`ComponentBase`) declare parameters that replace the attached properties:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `Tree` | `IWorkflowTreeViewModel?` | `null` | The tree to host. |
| `IsEnabled` | `bool` | `false` | Enables behavior wiring. |
| `ZoomEnabled` | `bool` | `false` | Enables wheel zoom. |
| `ScrollViewerId` | `string` | `"veloxdev-wf-scroll"` | `id` of the scroll element. |
| `CanvasId` | `string` | `"veloxdev-wf-canvas"` | `id` of the canvas element. |
| `GridDecorator` | `RenderFragment<SurfaceViewport>?` | `null` | Grid decorator fragment. |
| `Minimap` | `RenderFragment<SurfaceViewport>?` | `null` | Minimap fragment. |
| `ChildContent` | `RenderFragment<SurfaceCanvas>?` | `null` | The node/slot content. |
| `Background`, `GridColor`, `MajorGridColor`, `AxisColor` | `string` | CSS colors | Surface visuals. |
| `GridSpacing` | `double` | `40` | Minor grid spacing. |
| `MajorLineEvery` | `int` | `5` | Major-line cadence. |
| `RulerThickness` | `double` | `28` | Ruler band size. |

Public methods `OnWheelZoom(int wheelDelta, double scrollX, double scrollY, double viewportW, double viewportH, double reachW, double reachH)` and `OnSurfaceScroll(...)` are the JS callbacks; `DisposeAsync` unhooks them. The component renders the canvas and delegates node/link geometry to the browser through the Razor interop channel.

## Class: `WorkflowCanvasTransformBehavior`

Owns the canvas render transform used by node/link views. In XAML adapters node and link views bind their `RenderTransform` to the attached `(WorkflowCanvasTransformBehavior.Transform)` on the host; the surface behavior writes the pan offset here instead of using reflection.

| Adapter | Shape | Public API |
|---|---|---|
| WPF / WinUI / Jalium | `public static class` | attached `Transform` (WPF/WinUI: `System.Windows.Media.Transform`; Jalium: `Jalium.UI.Media.Transform`); `GetTransform(UIElement)`, `SetTransform(UIElement, Transform?)`, internal `Apply(UIElement, Transform)` |
| Avalonia | `public sealed class : AvaloniaObject` | `AttachedProperty<ITransform?>` `Transform`; `GetTransform(AvaloniaObject)`, `SetTransform(AvaloniaObject, ITransform?)`, internal `Apply(Control, ITransform)` |
| WinForms | `public static class` | stores an `Offset` (no render transform); `GetTransform(Control)`, `SetTransform(Control, Offset?)`, internal `Apply(Control, Offset)` |
| Razor | `public static class` | `GetOffset(IWorkflowTreeViewModel tree)` → `CanvasLayout.ActualOffset`; `ToCss(Offset)` → `translate(px, px)`; `GetTransformStyle(tree)` → CSS transform string |
| MAUI | not shipped | MAUI renders links through `WorkflowLinkOverlay` instead |

**Jalium note:** on Jalium the `ViewManager` mirrors the transform onto active node/link views' `RenderTransform`; the host itself never receives it.
