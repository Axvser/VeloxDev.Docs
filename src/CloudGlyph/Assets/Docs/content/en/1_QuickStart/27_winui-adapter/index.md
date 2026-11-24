# WinUI Adapter

`VeloxDev.WinUI` implements the same seven workflow roles for WinUI 3 / Windows App SDK. Its platform shape differs from the XAML desktop adapters in two important ways: the canvas pan is a composition translation, and the link view uses an **offset frame** so geometry never leaves the element's own box.

The reference implementation is `Examples/Workflow/WinUI Trimmed/Demo/Views/Workflow/` — read `TreeView.xaml` and `LinkView.xaml.cs` together, because they are the pair that implements the offset frame. "Trimmed" means **minimal demo**, not a publish setting.

WinUI has a demo but **no headless conformance suite**; `Src/Test/Headless/README.md` records that it has no windowless host.

## Pages

- [Prerequisites](00_prerequisites/index.md) — target frameworks, Windows App SDK and SDK.
- [Surface](01_surface/index.md) — project, generated ViewModels, named parts and the node template.
- [Interaction](02_interaction/index.md) — connection, the offset-frame link, routed input and the menu.
- [Verification and Complete Code](03_verification/index.md) — run checks and the full file set.
