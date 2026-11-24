# Avalonia Adapter

`VeloxDev.Avalonia` closes the same seven workflow roles as the WPF adapter, registered through `AvaloniaProperty` and resolved with `FindControl`. Compiled bindings are the default in the demos, so the templates carry a concrete `x:DataType`.

The reference implementation is `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/` — the project sits at `Demo/Demo/`, so the views are one level deeper than the WPF demo. "Trimmed" means **minimal demo**, not a publish setting.

## Pages

- [Prerequisites](00_prerequisites/index.md) — package, target frameworks and the Avalonia version.
- [Surface](01_surface/index.md) — project, generated ViewModels, the surface and the pooled node template.
- [Interaction](02_interaction/index.md) — connection, link rendering, routed input and the minimap.
- [Verification and Complete Code](03_verification/index.md) — the runnable file set and the run declaration.
