# Platform Adapters — API Reference

A platform adapter is the thin layer that turns the UI-framework-agnostic VeloxDev workflow engine into an interactive editor on one concrete UI framework. Each adapter is its own NuGet package (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`, `VeloxDev.Jalium`, source under `Src/Adapters/VeloxDev.*`) and ships the **same public namespace set**, so programs written against one adapter port to the others:

| Namespace | Purpose |
|---|---|
| `VeloxDev.WorkflowSystem.AttachedBehaviors` | Workflow attached behaviors and view containers: `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, and adapter-specific extras (`WorkflowLinkOverlay`, `WorkflowGridDecorator`, `WorkflowTreeView`, `IWorkflowTemplateSelector`) |
| `VeloxDev.TransitionSystem` | The adapter-provided transition surface — `Transition`, `Transition<T>`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter` (per-adapter members are documented in the `2_API/03_transition` feature) |
| `VeloxDev.DynamicTheme` | Theme value converters (`BrushConverter`, `DoubleConverter`, `PointConverter`, …). Not shipped by `VeloxDev.Jalium` (per-adapter converter sets are documented in the `2_API/04_dynamic-theme` feature) |
| `VeloxDev.Adapters.NativeSamplers` | One sampler class per framework value type (e.g. `BrushSampler`, `ThicknessSampler`, `PaddingSampler`) registered by that adapter's `Interpolator` |

A `dotnet new` item-template suite (`VeloxDev.{Platform}.Templates`, `Src/Templates/VeloxDev.*.Templates`) scaffolds the Node / Slot / Link / Tree / selector / grid-decorator / minimap views with the behaviors already connected.

> Evidence and coverage: workflow demos for every platform exist under `Examples/Workflow/<Platform>` (each with a `Trimmed` sibling) and reference these behaviors, so the behavior **names and shapes are source-verified on all seven adapters** (files under `Src/Adapters/VeloxDev.*/Attached/Workflow/*.cs`). The per-adapter **behavioral detail that a demo does not exercise is `*inferred*`** from source — it is not runtime-proven. WPF / Avalonia (and Razor via the Blazor demo) are the most exercised; this page marks each such claim.

## Adapter packages at a glance

| Package | Target frameworks (from `.csproj`) | Framework surface used |
|---|---|---|
| `VeloxDev.WPF` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0` | `System.Windows` (WPF) |
| `VeloxDev.Avalonia` | `netstandard2.0`; `net6.0` | Avalonia 11.1 (`Avalonia.Themes.Fluent`, `Avalonia.Fonts.Inter`) |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0`; `net10.0-windows10.0.19041.0` | Microsoft.WindowsAppSDK 1.6 / WinUI 3 |
| `VeloxDev.MAUI` | `net10.0`; `net10.0-windows10.0.19041.0` | .NET MAUI 10.0 (Microsoft.Maui.Controls), WinUI 3 on the Windows TFM |
| `VeloxDev.WinForms` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0` | `System.Windows.Forms` |
| `VeloxDev.Razor` | `net6.0` | Blazor / Razor (`Microsoft.NET.Sdk.Razor`, ASP.NET Core) |
| `VeloxDev.Jalium` | `net10.0` (platform-neutral) | Jalium.UI.Controls (cross-platform core only) |

All seven packages are `Version 8.0.0`, depend on `VeloxDev.Core` (project reference in `Debug`, package reference `8.0.0` otherwise), and expose the workflow engine, the transition engine, and the theme layer transitively.

> Cross-feature ownership: the **adapter-provided transition types** belong to the transition feature (`2_API/03_transition`, section `03_adapter-provided`), and the **adapter theme converters** belong to the dynamic-theme feature (`2_API/04_dynamic-theme`, page `04_PlatformAdapters`). This feature documents the adapters themselves, the workflow attached-behavior surface they all host, and the `dotnet new` view templates.

## Pages

- [attached-behaviors](00_attached-behaviors/index.md) — the shared workflow attached-behavior surface in `VeloxDev.WorkflowSystem.AttachedBehaviors`, documented once with per-adapter shapes (surface + canvas transform, view pool, node/slot behaviors, minimap, adapter-specific overlays).
- [adapter-catalogue](01_adapter-catalogue/index.md) — per-adapter reference: which behavior files, base classes, native samplers, and transition/theme wiring each package ships.
- [templates](02_templates/index.md) — the `dotnet new` item templates and their CLI options.
