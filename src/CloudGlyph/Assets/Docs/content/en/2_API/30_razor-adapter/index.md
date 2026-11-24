# Razor Adapter

`VeloxDev.Razor` expresses the workflow surface as a Blazor component tree. There are no attached properties: components expose `[Parameter]` values, and a static JavaScript module (`wwwroot/veloxdev.workflow.js`, shipped inside the package) owns the wheel gesture, element measurement and the zoom-frame curve refresh.

The assembly's workflow types are under `VeloxDev.WorkflowSystem.AttachedBehaviors`; transition types re-implement the shared engine, and the theme converters target CSS strings.

## Type groups

1. [Surface and view pool](00_surface-and-pool/index.md) — `WorkflowSurfaceBehavior`, `ViewPool`.
2. [Input components](01_input-components/index.md) — node drag, slot connection, slot layout and `SurfacePointerKind`.
3. [Overlays and decorators](02_overlays-and-decorators/index.md) — `WorkflowGridDecorator`, `WorkflowMinimapOverlay`.
4. [Presentation helpers](03_presentation-helpers/index.md) — canvas transform, events, geometry scope, presentation and runtime ids.
5. [JavaScript module](04_javascript-module/index.md) — the exports that back the interop and can be called by hand.
6. [Transition and theme](05_transition-and-theme/index.md) — the Razor transition types and `IThemeValueConverter` implementations.

Generation produces a `.razor` + `.razor.cs` pair for every role; the surface consumes the pair as one component.
