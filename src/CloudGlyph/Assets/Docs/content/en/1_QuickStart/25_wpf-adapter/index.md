# WPF Adapter

`VeloxDev.WPF` closes the Core workflow surface with WPF attached behaviors: a named-part surface, a pooled view host, node drag, slot connection, slot layout, a minimap, and the existing transition and theme bridges. This QuickStart builds a working editor surface in a `net8.0-windows` WPF application.

The reference implementation is `Examples/Workflow/WPF Trimmed/Demo/Views/Workflow/` — `TreeView.xaml` (the surface and both templates), `NodeView.xaml`, `SlotView.xaml`, `LinkView.xaml` and the ViewModels beside them. "Trimmed" means **minimal demo**, not a publish setting.

## Pages

- [Prerequisites](00_prerequisites/index.md) — package, target frameworks and SDK.
- [Surface](01_surface/index.md) — project, generated ViewModels, named parts and the pooled node template.
- [Interaction](02_interaction/index.md) — slot connection, link rendering, the input route, wheel/keys and the minimap.
- [Verification and Complete Code](03_verification/index.md) — the runnable file set and the run declaration.
