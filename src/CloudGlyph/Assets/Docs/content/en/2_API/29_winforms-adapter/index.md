# WinForms Adapter

`VeloxDev.WinForms` closes the shared platform contract with Easel: one `VisualHost`, a camera on `PART_Canvas`, a workflow-free view pool, and attached behaviors for slot measurement, node drag and slot connection. This section enumerates that surface by type group.

All workflow types are in the `VeloxDev.WinForms` assembly under `VeloxDev.WorkflowSystem.*`. Transition types re-implement the shared transition engine over Easel visuals; theme types convert `System.Drawing` values.

## Type groups

1. [Surface and view pool](00_surface-and-pool/index.md) — `WorkflowSurfaceBehavior`, `ViewPool`, `ViewPoolChangedEventArgs`, `WorkflowEvents`.
2. [Gesture behaviors](01_gesture-behaviors/index.md) — `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`.
3. [Overlays](02_overlays/index.md) — `WorkflowMinimapOverlay`, `WorkflowInfoOverlay`, `IWorkflowMinimapScrollSource`.
4. [View hosting](03_view-hosting/index.md) — the Core view-pool and minimap layers closed for Easel.
5. [Transition and animation](04_transition-and-animation/index.md) — `Interpolator`, `Transition<T>`, the sampler set and `EaselAnimationBootstrap`.
6. [Theme converters](05_theme-converters/index.md) — the `IThemeValueConverter` implementations for `System.Drawing` and WinForms value types.

The names the surface resolves on the template are stable across the seven adapters: `PART_Canvas`, `PART_ScrollViewer`, `PART_GridDecorator`, `PART_SurfaceBorder`, `PART_MinimapOverlay`, `PART_InfoOverlay` and the `WorkflowTemplateSelector` resource key.
