# Adapter decorators

Only the Razor adapter ships a decorator type. The XAML adapters ship an item template instead: the generated class is the same shape on each platform, with the platform's own drawing API. Every adapter still resolves the decorator through the same named-part or parameter contract.

## Razor: WorkflowGridDecorator

```csharp
namespace VeloxDev.WorkflowSystem.AttachedBehaviors;

public partial class WorkflowGridDecorator : ComponentBase, IWorkflowGridDecorator, IDisposable
```

A Razor component that mirrors a `WorkflowSurfaceBehavior`'s offsets and draws the tick layer.

### Parameters and properties

| Member | Declaration | Attribute | Default | Meaning |
|---|---|---|---|---:|
| `Viewport` | `SurfaceViewport? Viewport { get; set; }` | `[Parameter]` | `null` | Surface viewport context pushed by the behavior. |
| `ViewportFeed` | `SurfaceViewportFeed? ViewportFeed { get; set; }` | `[CascadingParameter]` | `null` | Feed the component subscribes to for cheap tick refreshes. |
| `RulerThickness` | `double RulerThickness { get; set; }` | `[Parameter]` | `28` | Ruler thickness in pixels. |
| `Spacing` | `double Spacing { get; set; }` | `[Parameter]` | `40` | Tick spacing in pixels. |
| `MajorLineEvery` | `int MajorLineEvery { get; set; }` | `[Parameter]` | `5` | Minor cells between labelled ticks. |
| `RulerBackground` | `string RulerBackground { get; set; }` | `[Parameter]` | `"rgba(37,37,38,0.78)"` | Ruler background color. |
| `TickColor` | `string TickColor { get; set; }` | `[Parameter]` | `"#555555"` | Tick color. |
| `LabelColor` | `string LabelColor { get; set; }` | `[Parameter]` | `"#888888"` | Numeric label color. |
| `DividerColor` | `string DividerColor { get; set; }` | `[Parameter]` | `"#3A3D40"` | Ruler divider color. |
| `AxisColor` | `string? AxisColor { get; set; }` | `[Parameter]` | `null` | World-0 tick color; falls back to `TickColor`. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | — | `0` | Pushed scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | — | `0` | Pushed content offsets. |
| `RulerBand` | `double RulerBand => RulerThickness` | — | — | Read-only band thickness. |

### Lifecycle

```csharp
protected override void OnInitialized();
protected override void OnParametersSet();
public void Dispose();
```

`OnInitialized` subscribes to `ViewportFeed.Changed`; `OnParametersSet` copies the pushed offsets and ensures the tick window; `Dispose` unsubscribes.

Labels format as an integer, then `K` at 10,000 or more and `M` at 1,000,000 or more.

## XAML item template

The seven packs expose a decorator item as `{prefix}-v-decorator`, with prefixes `wpf`, `ava`, `winui`, `maui`, `winforms`, `razor`, and `jalium`. The WPF identity is `VeloxDev.WPF.WorkflowGridDecorator`; its source file is `TemplateClass.cs` and its default name is `GridDecorator`.

The generated class is `Grid`-derived on XAML platforms and implements `IWorkflowGridDecorator`. Its public shape:

| Member | Type | Default |
|---|---|---:|
| `RulerThickness` | `double` | `28` |
| `GridSpacing` | `double` | `40` |
| `MajorLineEvery` | `int` | `5` |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` |
| `RulerBand` | `double` (read-only) | `RulerThickness` |

The template also parameterises the surface, minor, major, axis, ruler, tick, label, and divider colors. The generated constructor clips to bounds, creates a hit-test-transparent grid layer and ruler layer, puts the ruler above the content, and invalidates both on size change.

The adapters do not ship this type; generate it once per project with `dotnet new <prefix>-v-decorator`.

## GridDecoratorName across adapters

| Adapter | Declaration | Accessor element type |
|---|---|---|
| WPF | `DependencyProperty.RegisterAttached("GridDecoratorName", typeof(string), ...)` | `DependencyObject` |
| Avalonia | `AvaloniaProperty.RegisterAttached<WorkflowSurfaceBehavior, UserControl, string?>("GridDecoratorName")` | `AvaloniaObject` |
| WinUI | `DependencyProperty.RegisterAttached(...)` | `DependencyObject` |
| WinForms | `DependencyProperty.RegisterAttached(...)` | `Control` |
| MAUI | `BindableProperty.CreateAttached(...)` | `BindableObject` |
| Jalium | `DependencyProperty.RegisterAttached(...)` | `DependencyObject` |
| Razor | `[Parameter] public RenderFragment<SurfaceViewport>? GridDecorator { get; set; }` | — |

Every `GridDecoratorName` defaults to `null`. The behavior resolves the element by name in the `UserControl` namescope, and only pushes to it when it implements `IWorkflowGridDecorator`. Razor instead passes a render fragment that receives the current `SurfaceViewport`.

## Notes

- On XAML platforms the decorator must wrap the scroll viewer, not sit inside the canvas; it needs to paint at viewport size and see the scroll offsets.
- On Razor the component re-renders its tick layer from the viewport feed; a full surface render is not required.
- Set the name or fragment only when the capability is used; the surface tolerates a missing decorator.
