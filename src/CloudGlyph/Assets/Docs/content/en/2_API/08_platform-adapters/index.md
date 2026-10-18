# Platform Adapters — API Reference

A platform adapter is the thin layer that turns the UI-framework-agnostic VeloxDev workflow engine into an interactive editor on one concrete UI framework. Each adapter is its own NuGet package (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`, `VeloxDev.Jalium`, source under `Src/Adapters/VeloxDev.*`) and ships the **same public namespace set**, so programs written against one adapter port to the others:

| Namespace | Purpose |
|---|---|
| `VeloxDev.WorkflowSystem.AttachedBehaviors` | Workflow attached behaviors and view containers: `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`, `ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, and adapter-specific extras (`WorkflowLinkOverlay` on MAUI, `WorkflowLinkBounds` on Jalium, `WorkflowTreeView` / attachments / `WorkflowGridDecorator` / `IWorkflowTemplateSelector` on WinForms) |
| `VeloxDev.TransitionSystem` | The adapter-provided transition surface — `Transition`, `Transition<T>`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector`, `TransitionScheduler`, `TransitionInterpreter` (per-adapter members are documented in the `2_API/03_transition` feature) |
| `VeloxDev.DynamicTheme` | Theme value converters (`BrushConverter`, `DoubleConverter`, `PointConverter`, …). Not shipped by `VeloxDev.Jalium` (per-adapter converter sets are documented in the `2_API/04_dynamic-theme` feature) |
| `VeloxDev.Adapters.NativeSamplers` | One sampler class per framework value type (e.g. `BrushSampler`, `ThicknessSampler`, `PaddingSampler`) registered by that adapter's `Interpolator` |

A `dotnet new` item-template suite (`VeloxDev.{Platform}.Templates`, `Src/Templates/VeloxDev.*.Templates`) scaffolds the Node / Slot / Link / Tree / selector / grid-decorator / minimap views with the behaviors already connected.

> Evidence and coverage: workflow demos for every platform exist under `Examples/Workflow/<Platform>` (each with a `Trimmed` sibling) and reference these behaviors, so the behavior **names and shapes are source-verified on all seven adapters** (files under `Src/Adapters/VeloxDev.*/Attached/Workflow/*.cs`). The per-adapter **behavioral detail that a demo does not exercise is `*inferred*`** from source — it is not runtime-proven. WPF / Avalonia (and Razor via the Blazor demo) are the most exercised; this page marks each such claim.

## Adapter packages at a glance

| Package | Target frameworks (from `.csproj`) | Framework surface used |
|---|---|---|
| `VeloxDev.WPF` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0`; `net8.0-windows` | `System.Windows` (WPF) |
| `VeloxDev.Avalonia` | `netstandard2.0`; `net6.0`; `net8.0` | Avalonia 11.1.0 (`Avalonia.Themes.Fluent`, `Avalonia.Fonts.Inter`) |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0`; `net10.0-windows10.0.19041.0` | Microsoft.WindowsAppSDK 1.6.241114003 / WinUI 3 |
| `VeloxDev.MAUI` | `net10.0`; `net10.0-windows10.0.19041.0` | .NET MAUI 10.0.20 (Microsoft.Maui.Controls), WinUI 3 on the Windows TFM (WindowsAppSDK 1.7.250909003) |
| `VeloxDev.WinForms` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0`; `net8.0-windows` | `System.Windows.Forms` |
| `VeloxDev.Razor` | `net6.0`; `net8.0` | Blazor / Razor (`Microsoft.NET.Sdk.Razor`, ASP.NET Core) |
| `VeloxDev.Jalium` | `net10.0` (platform-neutral) | `Jalium.UI.Controls` 26.10.8 (cross-platform core only; demos add `Jalium.UI.Desktop` 26.10.9) |

All seven packages are `Version 10.0.0`, depend on `VeloxDev.Core` (project reference in `Debug`, package reference `10.0.0` otherwise), and expose the workflow engine, the transition engine, and the theme layer transitively. `VeloxDev.Jalium` is the exception for the theme layer: it ships no `VeloxDev.DynamicTheme` converters.

Connection preview is a Core facility the adapters call, not an adapter type: `WorkflowTreeEx.StandardSetPreviewReceiver` (extension on `IWorkflowTreeViewModel`) and `SlotHitTestEx.HitTest` live in Core under `VeloxDev.WorkflowSystem` (`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `.../GUI/Interaction/SlotHitTestEx.cs`).

> Cross-feature ownership: the **adapter-provided transition types** belong to the transition feature (`2_API/03_transition`, section `03_adapter-provided`), and the **adapter theme converters** belong to the dynamic-theme feature (`2_API/04_dynamic-theme`, page `04_PlatformAdapters`). This feature documents the adapters themselves, the workflow attached-behavior surface they all host, and the `dotnet new` view templates.

## Pages

- [attached-behaviors](00_attached-behaviors/index.md) — the shared workflow attached-behavior surface in `VeloxDev.WorkflowSystem.AttachedBehaviors`, documented once with per-adapter shapes (surface + canvas transform, view pool, node/slot behaviors, minimap, adapter-specific overlays).
- [adapter-catalogue](01_adapter-catalogue/index.md) — per-adapter reference: which behavior files, base classes, native samplers, and transition/theme wiring each package ships.
- [templates](02_templates/index.md) — the `dotnet new` item templates and their CLI options.
