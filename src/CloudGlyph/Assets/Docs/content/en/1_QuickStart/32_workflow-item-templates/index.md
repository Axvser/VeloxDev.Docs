# Workflow Item Templates

Each of the seven GUI adapters ships a `dotnet new` **item-template pack**. A pack is not a library and not a demo: it is a set of text items that generate the view layer into your own project, in your namespace and with your colours.

Every pack ships the same seven roles — one host (`tree`) and six parts — with the behaviours already wired.

| Package | Short-name prefix | Generated for |
| --- | --- | --- |
| `VeloxDev.WPF.Templates` | `wpf` | WPF |
| `VeloxDev.Avalonia.Templates` | `ava` | Avalonia 11 |
| `VeloxDev.WinUI.Templates` | `winui` | WinUI 3 / Windows App SDK |
| `VeloxDev.MAUI.Templates` | `maui` | .NET MAUI |
| `VeloxDev.WinForms.Templates` | `winforms` | Windows Forms over Easel |
| `VeloxDev.Razor.Templates` | `razor` | Blazor / Razor |
| `VeloxDev.Jalium.Templates` | `jalium` | Jalium |

Seven packs × seven roles = **49 short names**, all listed in [Generate a suite](01_generate-a-suite/index.md).

| Role | Item directory | Default class name | Suffix |
| --- | --- | --- | --- |
| tree | `workflow-tree-view` | `TreeView` | `-tree` |
| node | `workflow-node-view` | `NodeView` | `-node` |
| slot | `workflow-slot-view` | `SlotView` | `-slot` |
| link | `workflow-link-view` | `LinkView` | `-link` |
| selector | `workflow-template-selector` | `TemplateSelector` (`CustomTemplateSelector` on WinForms) | `-selector` |
| decorator | `workflow-grid-decorator` | `GridDecorator` | `-decorator` |
| minimap | `workflow-minimap-overlay` | `MinimapOverlay` | `-minimap` |

## What a pack does not give you

- **Not the ViewModels.** Tree, node, slot and link ViewModels, the node types and their helpers are yours.
- **Not the host shell.** `App`, `Program`, `MainWindow` / `MainPage` / `MainForm` come from the GUI project.
- **Not the link menu entries.** The tree declares and wires the menu; it ships empty.
- **Not the debug HUD.** The `InfoOverlay` readout in the demos is a host diagnostic, not a template item.

## Read in order

1. [Prerequisites and install](00_prerequisites/index.md) — SDK, the matching adapter package, install and uninstall, one namespace.
2. [Generate a suite](01_generate-a-suite/index.md) — the full 49 short names and the seven commands for each pack.
3. [Customise the generated views](02_customise/index.md) — style parameters, the selector, the link menu, platform differences.
4. [Verification and complete script](03_verification/index.md) — build is the check, common failures, a full generation script, the run declaration.
