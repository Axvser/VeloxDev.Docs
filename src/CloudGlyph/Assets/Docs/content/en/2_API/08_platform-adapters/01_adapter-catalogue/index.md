# API — Adapter Catalogue

Each adapter package ships the same three core namespaces (four where theme wiring exists). This page is the per-adapter reference; the shared workflow behavior **shapes** live under [00_attached-behaviors](../00_attached-behaviors/index.md), the per-adapter **transition/theme members** are documented in the transition and dynamic-theme features.

## Per-adapter surface

| Adapter | Namespaces shipped | Workflow behavior files (`Attached/Workflow/*`) |
|---|---|---|
| WPF | `AttachedBehaviors`, `TransitionSystem`, `DynamicTheme`, `Adapters.NativeSamplers` | `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay` |
| Avalonia | same four | the WPF set **plus** `PlatformDetection` (internal, touch-platform detection) |
| WinUI | same four | the WPF set |
| MAUI | same four | the WPF set **minus** `WorkflowCanvasTransformBehavior`; **plus** `WorkflowLinkOverlay` |
| WinForms | same four | the WPF set **plus** `NativeWindowStyleHelper` (internal); `ViewManager.cs` also declares `IWorkflowTemplateSelector` |
| Razor | same four | component set: `WorkflowSurfaceBehavior`, `ViewPool`, `WorkflowGridDecorator`, `WorkflowMinimapOverlay`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior` (`.razor` partial classes) **plus** static `WorkflowCanvasTransformBehavior`, `WorkflowGeometryScope`, `WorkflowRuntimeIds` |
| Jalium | `AttachedBehaviors`, `TransitionSystem`, `Adapters.NativeSamplers` (**no `DynamicTheme`**) | the WPF set **plus** `WorkflowGridDecorator`, `WorkflowTreeView`, and `IWorkflowTemplateSelector` |

### Class shapes per adapter

The **same public names** map to different framework base types; see the linked shape pages for each behavior's member table. In short:

| Behavior | WPF | WinUI | Jalium | Avalonia | MAUI | WinForms | Razor |
|---|---|---|---|---|---|---|---|
| `WorkflowSurfaceBehavior` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `ViewPool` | `sealed : DependencyObject` | `sealed : DependencyObject` | `static class` | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `ViewManager` ctor | `(Panel)` | `(Panel)` | `(Panel)` : `IDisposable` | `(Panel, IDataTemplate?)` | `(Layout)` | `(Control)` : `IDisposable` | n/a (component) |
| node/slot behaviors | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `WorkflowMinimapOverlay` | `FrameworkElement` | `Canvas` | `FrameworkElement` | `Control` | `GraphicsView : IDrawable` | `static class` (paints control) | `ComponentBase` |
| `WorkflowCanvasTransformBehavior` | static (attached DP) | static (attached DP) | static (attached DP) | `sealed : AvaloniaObject` | not shipped | static (holds `Offset`) | static (CSS) |

## Transition wiring per adapter (summary)

Every adapter provides, in `VeloxDev.TransitionSystem`, the full adapter surface: `Transition`, `Transition<T>`, `Transition<T>.StateSnapshot`, `TransitionEx`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter`, plus the platform samplers in `VeloxDev.Adapters.NativeSamplers`. Members are documented in the transition feature (`2_API/03_transition`, section `03_adapter-provided`).

| Adapter | Priority-typed? | Samplers registered (`Interpolator` static ctor) |
|---|---|---|
| WPF | `DispatcherPriority` (`Render`) | brushes/geometries via `BrushSampler`, `ThicknessSampler`, `PointSampler`, `CornerRadiusSampler`, `TransformSampler`, `SizeSampler`, `RectSampler`, `VectorSampler`, `ColorSampler`, `DropShadowEffectSampler`, `Point3DSampler`, `Vector3DSampler` |
| Avalonia | `DispatcherPriority` | Avalonia value types (`BrushSampler`, `ThicknessSampler`, `PixelPointSampler`, `BoxShadowsSampler`, `GridLengthSampler`, …) |
| WinUI | `DispatcherQueuePriority` (`High`) | WinUI types (`ProjectionSampler`, `GridLengthSampler`, …) |
| MAUI | non-priority | MAUI types (`PointFSampler`, `RectFSampler`, `SizeFSampler`, `ShadowSampler`, …) |
| WinForms | non-priority | `PaddingSampler` |
| Razor | non-priority | `StringSampler` |
| Jalium | `DispatcherPriority` | Jalium types incl. `Transform3DSampler` |

## Theme wiring per adapter (summary)

Theme value converters live in `VeloxDev.DynamicTheme` in each adapter assembly **except Jalium** (which ships no DynamicTheme layer). Full converter semantics are documented in the dynamic-theme feature (`2_API/04_dynamic-theme`, page `04_PlatformAdapters`).

| Adapter | Converter set |
|---|---|
| WPF / Avalonia / WinUI / MAUI | seven: `BrushConverter`, `ColorConverter`, `CornerRadiusConverter`, `DoubleConverter`, `ObjectConverter`, `PointConverter`, `ThicknessConverter` |
| WinForms | thirteen: the above (as `DoubleConverter`, `IntConverter`, `FloatConverter`, `PointConverter`, `PointFConverter`, `SizeConverter`, `SizeFConverter`, `RectangleConverter`, `RectangleFConverter`, `PaddingConverter`, `ColorConverter`, `FontConverter`, `ObjectConverter`) |
| Razor | four: `DoubleConverter`, `StringConverter`, `IntConverter`, `BoolConverter` |
| Jalium | none |
