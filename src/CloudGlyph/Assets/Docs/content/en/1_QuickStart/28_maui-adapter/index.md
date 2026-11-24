# MAUI Adapter

`VeloxDev.MAUI` closes the workflow surface for .NET MAUI. The host is a `ContentView`, the tree arrives as its `BindingContext`, and links are drawn by one viewport-sized `WorkflowLinkOverlay` instead of one pooled view per link. The adapter has no `WorkflowCanvasTransformBehavior`; the surface and the view arranger own the geometry.

The reference implementation is `Examples/Workflow/MAUI Trimmed/Demo/Controls/Workflow/` — note `Controls/`, not `Views/`. "Trimmed" means **minimal demo**, not a publish setting.

MAUI has a demo but **no headless conformance suite**; `Src/Test/Headless/README.md` records that it has no windowless host.

## Pages

- [Prerequisites](00_prerequisites/index.md) — target frameworks, the MAUI workload and package versions.
- [Surface](01_surface/index.md) — project, generated ViewModels, the content-view host and the node template.
- [Interaction](02_interaction/index.md) — node drag, connection, the shared link overlay, gestures and the menu.
- [Verification and Complete Code](03_verification/index.md) — run checks and the full file set.
