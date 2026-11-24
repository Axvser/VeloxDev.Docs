# Workflow Item Templates

Each of the seven GUI adapters ships a `dotnet new` **item-template pack**. A pack is not a library and not a demo: it is a set of text items that generate the view layer into your own project, in your namespace and with your colours.

Every pack ships the same seven roles — one host (`tree`) and six parts — with the behaviours already wired. Seven packs × seven roles = **49 short names**.

| Package | Short-name prefix | Generated for |
| --- | --- | --- |
| `VeloxDev.WPF.Templates` | `wpf` | WPF |
| `VeloxDev.Avalonia.Templates` | `ava` | Avalonia 11 |
| `VeloxDev.WinUI.Templates` | `winui` | WinUI 3 / Windows App SDK |
| `VeloxDev.MAUI.Templates` | `maui` | .NET MAUI |
| `VeloxDev.WinForms.Templates` | `winforms` | Windows Forms over Easel |
| `VeloxDev.Razor.Templates` | `razor` | Blazor / Razor |
| `VeloxDev.Jalium.Templates` | `jalium` | Jalium |

## Type groups

1. [Packages and roles](00_packages-and-roles/index.md) — package metadata, the seven roles, item identities and file counts.
2. [Short names](01_short-names/index.md) — the full 49-name matrix and the identity pattern per platform.
3. [Generation options](02_generation-options/index.md) — `-n`, `-ns`, `-o`, every style symbol and its aliases, inert values and defaults.
4. [Generated files](03_generated-files/index.md) — what each role emits, the wired behaviours, and the build gate.

## What a pack does not give you

- **Not the ViewModels.** Tree, node, slot and link ViewModels, node types and their helpers are yours.
- **Not the host shell.** `App`, `Program`, `MainWindow` / `MainPage` / `MainForm` come from the GUI project.
- **Not the link menu entries.** The tree declares and wires the menu; it ships empty.
- **Not the debug HUD.** The `InfoOverlay` readout in the demos is a host diagnostic, not a template item.

The `* Trimmed` demos are minimal-call-sequence mirrors of the generated roles. They are not publish-trim or AOT validation runs.
