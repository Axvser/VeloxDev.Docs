# Platform Adapters — API Reference

The six GUI adapters (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`) share the same behavior surface in the `VeloxDev.WorkflowSystem.AttachedBehaviors` namespace, plus per-platform transition/theme wiring in `VeloxDev.TransitionSystem` / `VeloxDev.DynamicTheme`. Verified names come from the WPF adapter source and the WPF/Avalonia/Blazor demos; anything not exercised by a demo is marked `*inferred*`.

## Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`

Every adapter ships these types. WPF/Avalonia/Razor are demo-exercised; WinUI/MAUI/WinForms expose the same names (source-verified) but their per-platform behavior detail is `*inferred*`.

### Class: `WorkflowSurfaceBehavior`

Attached behavior for the workflow surface host (a `UserControl`). Owns panning, pointer tracking, the visible-region update, and the grid/minimap feed.

| Member | Type / Signature | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Master switch. When `true`, the behavior attaches to the host's `Loaded` / `Unloaded` / `DataContextChanged` / mouse events. |
| `ScrollViewerName` | attached `string?` | Name of the inner `ScrollViewer` (e.g. `PART_ScrollViewer`). |
| `CanvasName` | attached `string?` | Name of the inner `Canvas` (e.g. `PART_Canvas`). |
| `GridDecoratorName` | attached `string?` | Name of the element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | attached `string?` | Element whose press starts panning (the surface border). |
| `MinimapOverlayName` | attached `string?` | Name of the element implementing `IWorkflowMinimapOverlay`. |
| `Refresh` | `static void Refresh(UserControl host)` | Re-resolves named controls, re-applies layout, and updates the visible region. Called on load, scroll, and `DataContextChanged`. |

**Behavior (verified, WPF):** panning starts only on "blank" surface clicks (not over node/slot visuals or the scrollbar), `SetPointerCommand` is fed the canvas-space pointer, `GetHelper().Viewport` is updated from the scroll offsets, and `Layout.ViewportOffset` is persisted for serialization round-trips.

### Static Class: `WorkflowCanvasTransformBehavior`

Owns the canvas render transform used by node/link views.

| Member | Type / Signature | Description |
|---|---|---|
| `Transform` | attached `Transform?` | Node and link views bind `RenderTransform` to `(behaviors:WorkflowCanvasTransformBehavior.Transform)` on the host. |
| `Apply` | `internal static void Apply(UIElement, Transform)` | `WorkflowSurfaceBehavior` writes the pan offset here instead of using reflection. |

### Class: `ViewPool`

Attached object-pool support for a `Panel`.

| Member | Type / Signature | Description |
|---|---|---|
| `ItemsSource` | attached `INotifyCollectionChanged?` | e.g. `behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"`. |
| `TemplateSelector` | attached `DataTemplateSelector?` | Selects the item template per view-model type. |

### Class: `ViewManager`

Sealed per-panel manager (created by `ViewPool`). Pools views per `Type` in a `Queue<FrameworkElement>`, keeps active views + a pending batch, and renders in batches of **3** per dispatcher `Background` tick. Removed items are collapsed (`Visibility.Collapsed`), unbound, and returned to the pool. Template lookup order: `ViewPool.TemplateSelector` → resources walk → `Application.Current.Resources`. *Verified in WPF; the Avalonia/MAUI/WinUI/WinForms `ViewManager` follows the same pattern (`*inferred*` for identical batch-size behavior).*

### Class: `WorkflowNodeDragBehavior`

Attached behavior that makes a node draggable.

| Member | Type / Signature | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Enables capture + move handling. |
| `CoordinateHostName` | attached `string?` | Name of the element whose coordinate space is used for the delta. |
| `CoordinateHostType` | attached `Type?` | Fallback host type; defaults to `Canvas`. |

On press it captures the mouse; on move it executes `node.MoveCommand.Execute(new Offset(current - last))`; on release/lost-capture it stops.

### Class: `WorkflowSlotConnectionBehavior`

Attached behavior that connects slots by press/release.

| Member | Type / Signature | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Enables press/release handling. |

On press it executes `slot.SendConnectionCommand.Execute(null)`; on release `slot.ReceiveConnectionCommand.Execute(null)`.

### Class: `WorkflowSlotLayoutBehavior`

Keeps slot anchors in sync with the node layout.

| Member | Type / Signature | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Enables the layout sync. |
| `SlotNames` | attached `string?` | Comma-separated names of single slot controls (e.g. `PART_InputSlot`). |
| `SlotEnumeratorNames` | attached `string?` | Comma-separated names of `ItemsControl`s enumerating slots (e.g. `PART_OutputSlots`). |
| `CoordinateHostName` | attached `string?` | Coordinate space for computing the anchor. |
| `CoordinateHostType` | attached `Type?` | Fallback host type; defaults to `Canvas`. |

It watches the node's `Anchor`/`Size`/slot properties and re-computes each slot's `Anchor` (accounting for `Layout.ActualOffset`), using `TranslatePoint` to find the slot center.

### Class: `WorkflowMinimapOverlay`

`FrameworkElement : IWorkflowMinimapOverlay` (WPF/Avalonia/WinUI/MAUI). Renders a thumbnail of all nodes/links plus a draggable viewport indicator.

| Property | Type | Notes |
|---|---|---|
| `ScrollOffsetX/Y`, `ContentOffsetX/Y` | `double` | Fed by the surface behavior. |
| `WorkflowTree` | `IWorkflowTreeViewModel?` | Subscribes to node/link collections for dirty tracking. |
| `ViewportWidth/Height` | `double` | The visible viewport size. |
| `IsMinimapVisible` | `bool` | Toggles rendering. |
| `MinimapWidth/Height` | `double` | Defaults 200 × 140. |
| `RulerThickness`, `LinkStrokeThickness` | `double` | Visual metrics. |
| `MinimapBackground/BorderBrush`, `NodeBrush`, `LinkBrush`, `ViewportStroke/Fill`, `ViewportStrokeThickness` | `Brush` / `double` | Visuals. |
| `ScrollViewerName` | `string?` | Resolved on load to enable drag-to-navigate. |

Drag logic (verified, WPF): pressing inside the viewport rect keeps it in place and aligns it to the cursor; pressing elsewhere moves the viewport block center to the cursor, clamped inside the minimap. `NavigateToWorld` converts minimap space back to world coordinates and scrolls the `ScrollViewer`, growing `Layout.NegativeOffset`/`PositiveOffset` at the edges.

### Interface: `IWorkflowGridDecorator`

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
}
```

Implemented by grid decorator views (e.g. `GridDecorator` from `wpf-v-decorator`) so `WorkflowSurfaceBehavior` can push offsets without reflection.

### Interface: `IWorkflowMinimapOverlay`

```csharp
public interface IWorkflowMinimapOverlay
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double ViewportWidth { get; set; }
    double ViewportHeight { get; set; }
    IWorkflowTreeViewModel? WorkflowTree { get; set; }
    bool IsMinimapVisible { get; set; }
}
```

## Namespace: `VeloxDev.TransitionSystem` (per-platform wiring)

Each adapter provides `Interpolator`, `TransitionEffect`, `TransitionEffects`, `UIThreadInspector`, `State`, and the `Interpolators/*` set. See the [Transition System](1_TransitionSystem) API page for the base engine.

### Class: `Interpolator`

`Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>`. The static constructor registers platform types:

| Adapter | Registered types (static ctor) |
|---|---|
| WPF | `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D` |
| Avalonia | `IBrush`, `ITransform`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows`, `GridLength` |
| WinUI | `Brush`, `Color`, `CornerRadius`, `GridLength`, `Point`, `Projection`, `Rect`, `Size`, `Thickness`, `Transform` |
| MAUI | `Brush`, `Color`, `CornerRadius`, `Point`, `PointF`, `Rect`, `RectF`, `Shadow`, `Size`, `SizeF`, `Thickness`, `Transform` |
| WinForms | `Padding` |
| Razor | `string` → `StringInterpolator` |

The `Interpolators/*` folder holds one class per type (e.g. `BrushInterpolator`, `ThicknessInterpolator`, `TransformInterpolator`, `CornerRadiusInterpolator`, `PointInterpolator`, `ColorInterpolator`, `DropShadowEffectInterpolator`, `Point3DInterpolator`, `Vector3DInterpolator`, `SizeInterpolator`, `RectInterpolator`, `VectorInterpolator` for WPF). Interpolator classes for non-WPF platforms are source-verified to exist; the exact registration list is `*inferred*` from the type names plus the old wiki for Avalonia.

### Class: `TransitionEffect`

`TransitionEffect : TransitionEffectCore<TPriorityCore>`. Default priority:

| Adapter | Priority type | Default priority |
|---|---|---|
| WPF | `DispatcherPriority` | `DispatcherPriority.Render` |
| Avalonia | `DispatcherPriority` | `DispatcherPriority.Render` |
| WinUI | `DispatcherQueuePriority` | `DispatcherQueuePriority.High` |
| MAUI / WinForms / Razor | none | n/a (no priority generic argument) |

### Class: `TransitionEffects`

Static presets: `Empty` (`Duration = TimeSpan.Zero`), `Theme` (`0.46 s`), `Hover` (`0.32 s`). **Note:** `TransitionEffects` is a **non-static** class in the WinUI adapter (members are still `static`); everywhere else it is `public static class TransitionEffects`.

### Class: `UIThreadInspector`

`UIThreadInspector : UIThreadInspectorCore[<TPriorityCore>]`. Marshals frame writes to the UI thread:

| Adapter | Thread source | Notes |
|---|---|---|
| WPF | `Application.Current?.Dispatcher` | Prefers the target `DispatcherObject`'s own dispatcher; falls back to `Application.Current`. |
| Avalonia | `Dispatcher.UIThread` | Uses `CheckAccess` / `InvokeAsync`. |
| WinUI | `DispatcherQueue` | Lazily captures `DispatcherQueue.GetForCurrentThread()`; explicit `static CaptureUIThread()`. A `DependencyObject` target uses its own queue. *An earlier wiki description mentioned a `SetWindow(Window)` requirement — not present in the current source.* |
| MAUI | `Application.Current?.Dispatcher` | `IsUIThread()` == `IsDispatchRequired == false`. |
| WinForms | `SynchronizationContext` + `static CaptureUIThread()` | Target `Control` marshals via `Control.Invoke` / `BeginInvoke` when the handle exists. |
| Razor | `SynchronizationContext` + `static CaptureUIThread()` | Also `static NotifyShutdown()`. |

### Class: `State`

`public class State : StateCore { }` — adapter-specific state bag (empty subclass of the core implementation). *Verified WPF/Avalonia; same shape elsewhere (`*inferred*`).*

### Class: `StateSnapshot` — `.Property(...)` overload set

Each overload is `StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`:

| Adapter | Extra overloads (beyond numerics + `System.Drawing.*` + `System.Numerics.*`) |
|---|---|
| WPF | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `CornerRadius`, `Thickness`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect?`, `Point3D`, `Vector3D` |
| Avalonia | `IInterpolable?`, `ITransform?`, `IBrush?`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows` |
| WinUI | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `CornerRadius`, `Thickness`, `Projection?`, `Size`, `Rect`, `GridLength`, `Color` |
| MAUI | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `PointF`, `CornerRadius`, `Thickness`, `Color?`, `Size`, `SizeF`, `Rect`, `RectF`, `Shadow?` |
| WinForms | `IInterpolable?`, `Padding` |
| Razor | `string?` (no `IInterpolable?`) |

## Namespace: `VeloxDev.DynamicTheme` (per-platform)

Each adapter ships `IThemeValueConverter` implementations. WPF (verified): `DoubleConverter`, `PointConverter`, `ThicknessConverter`, `CornerRadiusConverter`, `ColorConverter`, `BrushConverter`, `ObjectConverter` — each implements `object? Convert(Type targetType, string propertyName, object?[] parameters)`. Other adapters ship the same converter set (`*inferred*` from matching files). `ThemeManager.SetPlatformInterpolator(new Interpolator())` must be called once before animated theme switching.

## Templates: `VeloxDev.WPF.Templates` (and sibling packages)

`dotnet new` item templates. Short names (verified in `template.json`):

| Template | Short name | Default name | Generates |
|---|---|---|---|
| Node view | `wpf-v-node` | `NodeView` | `TemplateClass.xaml/.cs` |
| Slot view | `wpf-v-slot` | `SlotView` | `TemplateClass.xaml/.cs` |
| Link view | `wpf-v-link` | `LinkView` | `TemplateClass.xaml/.cs` |
| Tree view | `wpf-v-tree` | `TreeView` | `TemplateClass.xaml/.cs` |
| Template selector | `wpf-v-selector` | `TemplateSelector` | `TemplateClass.cs` |
| Grid decorator | `wpf-v-decorator` | `GridDecorator` | `TemplateClass.cs` |
| Minimap overlay | `wpf-v-minimap` | `MinimapOverlay` | `TemplateClass.cs` |

Style aliases (README-verified; Avalonia/WinUI/MAUI suites expose the same options):

| Template | Style aliases |
|---|---|
| Node | `-bg`, `-fg`, `-bb`, `-bt`, `-cr` |
| Slot | `-bg`, `-sc`, `-bc`, `-sp` |
| Link | `-lc`, `-lt` |
| Tree | `-bg`, `-bb`, `-bt`, `-cr` |
| Grid decorator | `-bg`, `-mic`, `-mac`, `-ac`, `-gs`, `-mle`, `-rb`, `-rtc`, `-rlc`, `-rdc` |
| Minimap overlay | `-bg`, `-bdr`, `-nf`, `-vs` |

All templates use `-ns` for the generated namespace.
