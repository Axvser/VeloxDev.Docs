# API — Attached Behaviors · WorkflowSurfaceBehavior & Canvas Transform

## Class: `WorkflowSurfaceBehavior`

Attached behavior for the workflow surface host — the control that owns the `ScrollViewer` + `Canvas` pair of the editor. It resolves named child controls, feeds the scroll/content offsets to the grid decorator and minimap, starts panning on "blank" surface presses, and hooks the zoom gesture.

Per adapter, the host element type and the property registration differ:

| Adapter | Host element | Declared as | Registration |
|---|---|---|---|
| WPF / WinUI | `UserControl` | `sealed class : DependencyObject` | `DependencyProperty.RegisterAttached` |
| Avalonia | `UserControl` | `sealed class : AvaloniaObject` | `AvaloniaProperty.RegisterAttached<WorkflowSurfaceBehavior, UserControl, T>` |
| MAUI | `ContentView` | `sealed class` | `BindableProperty.CreateAttached` |
| WinForms | `Control` | `sealed class` | private `ConditionalWeakTable<Control, SurfaceState>` |
| Razor | n/a (component) | `partial class WorkflowSurfaceBehavior : ComponentBase, IAsyncDisposable` | parameters |
| Jalium | `FrameworkElement` | `public static class` | `DependencyProperty.RegisterAttached` |

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
| `LinkMenuKey` | `string?` | `null` | Resource key of the link context menu (`ContextMenu` / `MenuFlyout`) the behavior shows on a link's right press; `null` means links have no menu. A key, not the menu itself, so the reference is not resolved before the dictionary that defines it. |

### Static method: `Refresh(host)`

Re-resolves named controls, re-applies layout, and pushes the visible region to the grid decorator and minimap. Invoked on load, scroll, `DataContextChanged`, and after pan/zoom updates.

| Adapter | Signature |
|---|---|
| WPF / Avalonia / WinUI | `public static void Refresh(UserControl host)` |
| MAUI | `public static void Refresh(ContentView host)` |
| WinForms | `public static void Refresh(Control host)` |
| Jalium | `public static void Refresh(FrameworkElement host)` |

**Jalium also exposes** `NavigateToWorld(FrameworkElement host, double worldX, double worldY)`, `NotifyZoomCommitted(FrameworkElement host)` / `NotifyZoomCommitted(FrameworkElement host, double horizontalOffset, double verticalOffset)`, and `TreeOf(DependencyObject element)`. The surface is a `static class`: it resolves the template's `PART_*` parts and feeds the viewport itself, exactly like the other adapters.

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
| `LinkMenu` | `RenderFragment<IWorkflowLinkViewModel>?` | `null` | Entries of the link context menu; the surface renders the chrome and owns the whole wiring (right press, positioning, open/close, `WorkflowInput.IsSuspended`). Each entry receives the link it acts on. |

Public methods `OnWheelZoom(int wheelDelta, double scrollX, double scrollY, double viewportW, double viewportH, double reachW, double reachH)` and `OnSurfaceScroll(...)` are the JS callbacks; `DisposeAsync` unhooks them. The component renders the canvas and delegates node/link geometry to the browser through the Razor interop channel.

### Link context menu

The surface behavior is what turns a link's right press into a menu. It subscribes to the tree's input route — `WorkflowInput.For(tree)`, one instance per tree, exposed through `IInputEvents.Input` — specifically its `PointerPressed` event. On a right press whose `Target` is an `IWorkflowLinkViewModel`, it resolves the resource named by `LinkMenuKey`, sets the menu's own `DataContext` to that link, converts the world point to screen coordinates, and opens the menu. While the menu is open it sets `WorkflowInput.IsSuspended = true`, so pointer tracking does not clear the hover the menu is about; it also subscribes to the helper's `LinkRemoved` and closes the menu if that link leaves the tree. `WorkflowInput` exposes the current `PointerTarget`, `HoveredLink`, `ConnectionSender`, `PreviewReceiver`, `PreviewState`, and `PreviewCheck`, plus `PreviewChanged` / `PreviewValidating`. The menu's entries are the host's: each binds the link it receives (`Command="{Binding DeleteCommand}"` on WPF/Avalonia/WinUI/MAUI, `@onclick` on Razor).

WinForms has no surface attached property for this; its `WorkflowTreeView` builds the menu through the overridable `OnBuildLinkMenu(menu, link)` hook instead, whose base implementation adds a single **Delete** item (the generated template overrides it with an empty menu). Jalium uses `LinkMenuKey` like the other XAML adapters: `WorkflowSurfaceBehavior` resolves the keyed `ContextMenu` and shows it on a link's right press.

## Class: `WorkflowCanvasTransformBehavior`

Owns the canvas render transform used by node/link views. In XAML adapters node and link views bind their `RenderTransform` to the attached `(WorkflowCanvasTransformBehavior.Transform)` on the host; the surface behavior writes the pan offset here instead of using reflection.

| Adapter | Shape | Public API |
|---|---|---|
| WPF / WinUI | `public static class` | attached `Transform` (`System.Windows.Media.Transform`); `GetTransform(UIElement)`, `SetTransform(UIElement, Transform?)`, internal `Apply(UIElement, Transform)` |
| Avalonia | `public sealed class : AvaloniaObject` | `AttachedProperty<ITransform?>` `Transform`; `GetTransform(AvaloniaObject)`, `SetTransform(AvaloniaObject, ITransform?)`, internal `Apply(Control, ITransform)` |
| WinForms | `public static class` | stores an `Offset` (no render transform); `GetTransform(Control)`, `SetTransform(Control, Offset?)`, internal `Apply(Control, Offset)` |
| Razor | `public static class` | `GetOffset(IWorkflowTreeViewModel tree)` → `CanvasLayout.ActualOffset`; `ToCss(Offset)` → `translate(px, px)`; `GetTransformStyle(tree)` → CSS transform string |
| MAUI | not shipped | MAUI renders links through `WorkflowLinkOverlay` instead |
| Jalium | not shipped as a separate class | `WorkflowSurfaceBehavior.CanvasTransform` is an attached `DependencyProperty` of type `Transform?`; the pooled Node/Link templates bind their `RenderTransform` to it |
