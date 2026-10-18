# API — Adapter Catalogue

Each adapter package ships the same three core namespaces (four where theme wiring exists). This page is the per-adapter reference; the shared workflow behavior **shapes** live under [attached-behaviors](../00_attached-behaviors/index.md), the per-adapter **transition/theme members** are documented in the transition and dynamic-theme features.

## Per-adapter surface

| Adapter | Namespaces shipped | Workflow behavior files (`Attached/Workflow/*`) |
|---|---|---|
| WPF | `AttachedBehaviors`, `TransitionSystem`, `DynamicTheme`, `Adapters.NativeSamplers` | `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, `WorkflowEvents` |
| Avalonia | same four | the WPF set |
| WinUI | same four | the WPF set |
| MAUI | same four | `WorkflowSurfaceBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, `WorkflowEvents`, **plus** `WorkflowLinkOverlay`; **no** `WorkflowCanvasTransformBehavior` |
| WinForms | same four | `WorkflowTreeView`, `WorkflowNodeAttachment`, `WorkflowSlotAttachment`, `WorkflowLinkAttachment`, `WorkflowGridDecorator`, `WorkflowMinimapOverlay` (both `Panel` subclasses), `WorkflowTemplateSelector`, `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowBindingExtensions`, paint helpers `WorkflowSurfaceColors` / `WorkflowSurfaceGraphics` / `WorkflowSurfaceGrid`, `SvgPathParser`, `IWorkflowMinimapScrollSource`, `IWorkflowSurfaceNodeView`, `ModelChangeRelay`, and `NativeWindowStyleHelper` (internal); `ViewManager.cs` also declares `IWorkflowTemplateSelector` |
| Razor | same four | component set: `WorkflowSurfaceBehavior`, `ViewPool`, `WorkflowGridDecorator`, `WorkflowMinimapOverlay`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior` (`.razor` partial classes) **plus** static `WorkflowCanvasTransformBehavior`, `WorkflowGeometryScope`, `WorkflowRuntimeIds`, `WorkflowPresentation`, and the `SurfacePointerKind` enum |
| Jalium | `AttachedBehaviors`, `TransitionSystem`, `Adapters.NativeSamplers` (**no `DynamicTheme`**) | `WorkflowSurfaceBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, `WorkflowLinkBounds`, `WorkflowEvents`; **no** separate `WorkflowCanvasTransformBehavior` (the surface exposes `CanvasTransform`), and no `WorkflowTreeView` / attachments / `IWorkflowTemplateSelector` — the templates supply the grid decorator and a `DataTemplateSelector` |

### Class shapes per adapter

The **same public names** map to different framework base types; see the linked shape pages for each behavior's member table. In short:

| Behavior | WPF | WinUI | Jalium | Avalonia | MAUI | WinForms | Razor |
|---|---|---|---|---|---|---|---|
| `WorkflowSurfaceBehavior` | `sealed : DependencyObject` | `sealed : DependencyObject` | `static class` (attached DPs; host `FrameworkElement`) | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `ViewPool` | `sealed : DependencyObject` | `sealed : DependencyObject` | `static class` | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `ViewManager` ctor | `(Panel)` | `(Panel)` | `(Panel)` : `IDisposable` | `(Panel, IDataTemplate?)` | `(Layout)` | `(Control)` : `IDisposable` | n/a (component) |
| node/slot behaviors | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : AvaloniaObject` | `sealed` (attached `BindableProperty`) | `sealed` (state table) | `ComponentBase` |
| `WorkflowMinimapOverlay` | `FrameworkElement` | `Canvas` | `FrameworkElement` | `Control` | `GraphicsView : IDrawable` | `Panel` (paints itself) | `ComponentBase` |
| `WorkflowCanvasTransformBehavior` | static (attached DP) | static (attached DP) | not shipped — `WorkflowSurfaceBehavior.CanvasTransform` attached DP | `sealed : AvaloniaObject` | not shipped | static (holds `Offset`) | static (CSS) |

## Transition wiring per adapter (summary)

Every adapter provides, in `VeloxDev.TransitionSystem`, the full adapter surface: `Transition`, `Transition<T>`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter`, plus the platform samplers in `VeloxDev.Adapters.NativeSamplers`. Members are documented in the transition feature (`2_API/03_transition`, section `03_adapter-provided`).

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
