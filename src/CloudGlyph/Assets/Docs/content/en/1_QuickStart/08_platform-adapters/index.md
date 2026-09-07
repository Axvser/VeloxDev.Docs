# Platform Adapters — Quick Start

## Platform Adapters

### Overview

VeloxDev's **workflow engine** (`VeloxDev.Core`) is UI-framework-agnostic: the tree model (`IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel`), the `WorkflowBuilder.Tree` source generator, and the spatial/compile machinery know nothing about WPF or MAUI. A **platform adapter** is the thin layer that turns that engine into a real, interactive editor on one GUI framework.

VeloxDev ships **seven adapters**, each as its own NuGet package, plus a matching `dotnet new` template pack:

| Adapter package | GUI framework | Template pack | Template prefix |
|---|---|---|---|
| `VeloxDev.WPF` | Windows Presentation Foundation | `VeloxDev.WPF.Templates` | `wpf-v-*` |
| `VeloxDev.WinForms` | Windows Forms | `VeloxDev.WinForms.Templates` | `winforms-v-*` |
| `VeloxDev.Avalonia` | Avalonia 11 | `VeloxDev.Avalonia.Templates` | `ava-v-*` |
| `VeloxDev.WinUI` | WinUI 3 (Windows App SDK) | `VeloxDev.WinUI.Templates` | `winui-v-*` |
| `VeloxDev.MAUI` | .NET MAUI | `VeloxDev.MAUI.Templates` | `maui-v-*` |
| `VeloxDev.Razor` | Razor / Blazor | `VeloxDev.Razor.Templates` | `razor-v-*` |
| `VeloxDev.Jalium` | Jalium UI | `VeloxDev.Jalium.Templates` | `jalium-v-*` |

An adapter provides, per framework:

- **Workflow attached behaviors** — under the namespace `VeloxDev.WorkflowSystem.AttachedBehaviors`: `WorkflowSurfaceBehavior` (the pan/zoom/scroll host), `WorkflowCanvasTransformBehavior` (the shared canvas transform), `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, plus the object-pooled view container (`ViewPool` bound to `Helper.VisibleItems`, recycling through `ViewManager`). The exact file set is per framework — e.g. MAUI routes its link layer through `WorkflowLinkOverlay` and has no separate canvas-transform behavior, while Razor implements several as `.razor` components.
- **Grid & minimap contracts** — the shared Core interfaces `IWorkflowGridDecorator` and `IWorkflowMinimapOverlay` (namespace `VeloxDev.WorkflowSystem`) that the surface behavior feeds scroll/content offsets into each pass; `WorkflowMinimapOverlay` supplies the default minimap logic and drag navigation.
- **Transition & theme wiring** — the closed per-framework types under `VeloxDev.TransitionSystem` (`Interpolator`, `State`, `Transition`, `TransitionEffects`, `TransitionInterpreter`, `TransitionScheduler`, `UIThreadInspector`) and — where the framework needs adapter-specific value types — the platform converters under `VeloxDev.DynamicTheme` (`ColorConverter`, `BrushConverter`, `CornerRadiusConverter`, …; Jalium's `PlatformAdapters` currently defines no converter set).

The **template packs** (`VeloxDev.{Platform}.Templates`) scaffold the same seven-view suite on every platform — node / slot / link / tree / template-selector / grid-decorator / minimap-overlay views with the behaviors already wired. This Quick Start walks the **WPF** path end to end (it has both demos and a complete template suite); the other adapters expose the same type names and namespace, so the same steps apply with their own prefix and framework host.

### Scope of this page

WPF is the exercised walkthrough. Where a non-WPF detail can only be read from source (no demo exercises it), the page marks it as `*inferred*`.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — target frameworks taken from each adapter's `.csproj`, SDK/workloads, demos
- [01 Install & Add Dependency](01_install/index.md) — the seven adapter packages and their template packs
- [02 Setup — Generate the Seven Views](02_setup/index.md) — run the `wpf-v-*` item templates and see what each file wires
- [03 Core Usage](03_core-usage/index.md) — host the surface, virtualize with `ViewPool`, drag nodes, connect slots, add grid/minimap, wire themes
- [04 Verification](04_verification/index.md) — observable results and the in-repo demo to run
- [05 Complete Code](05_complete-code/index.md) — the exact generated scaffold, one page per source file
