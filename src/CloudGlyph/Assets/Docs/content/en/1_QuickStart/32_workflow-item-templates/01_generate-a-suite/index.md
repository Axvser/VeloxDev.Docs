# Generate a suite

A suite is one host plus six parts. Generate all seven: the decorator draws the floating ruler bands, the minimap supplies the thumbnail, and the tree type-references the rest.

## The 49 short names

Every short name is `{prefix}-v-{suffix}`. The seven packs and seven roles give this matrix.

| Role | WPF | Avalonia | WinUI | MAUI | WinForms | Razor | Jalium |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tree | `wpf-v-tree` | `ava-v-tree` | `winui-v-tree` | `maui-v-tree` | `winforms-v-tree` | `razor-v-tree` | `jalium-v-tree` |
| node | `wpf-v-node` | `ava-v-node` | `winui-v-node` | `maui-v-node` | `winforms-v-node` | `razor-v-node` | `jalium-v-node` |
| slot | `wpf-v-slot` | `ava-v-slot` | `winui-v-slot` | `maui-v-slot` | `winforms-v-slot` | `razor-v-slot` | `jalium-v-slot` |
| link | `wpf-v-link` | `ava-v-link` | `winui-v-link` | `maui-v-link` | `winforms-v-link` | `razor-v-link` | `jalium-v-link` |
| selector | `wpf-v-selector` | `ava-v-selector` | `winui-v-selector` | `maui-v-selector` | `winforms-v-selector` | `razor-v-selector` | `jalium-v-selector` |
| decorator | `wpf-v-decorator` | `ava-v-decorator` | `winui-v-decorator` | `maui-v-decorator` | `winforms-v-decorator` | `razor-v-decorator` | `jalium-v-decorator` |
| minimap | `wpf-v-minimap` | `ava-v-minimap` | `winui-v-minimap` | `maui-v-minimap` | `winforms-v-minimap` | `razor-v-minimap` | `jalium-v-minimap` |

The suffix is `-decorator`, not `-grid`. The identity behind each item is `VeloxDev.<Platform>.Workflow<Role>`, for example `VeloxDev.WinForms.WorkflowTreeView`.

## The seven commands

One pack, all seven roles, one namespace:

```powershell
dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views
dotnet build
```

Change the prefix to target another GUI (`wpf`, `ava`, `winui`, `maui`, `razor`, `jalium`). Keep `-ns` identical across the seven.

| GUI | Selector's default name | Files per suite |
| --- | --- | --- |
| WPF, Avalonia, WinUI, MAUI, WinForms, Jalium | `TemplateSelector` (`CustomTemplateSelector` on WinForms) | 11: four markup pairs + three `.cs` |
| Razor | `TemplateSelector` | 14: seven `.razor` + `.razor.cs` pairs |

The per-GUI command blocks for WinForms, Razor and Jalium are in their adapter quick starts: [WinForms](../../29_winforms-adapter/01_surface-and-host/index.md), [Razor](../../30_razor-adapter/01_surface-and-host/index.md), [Jalium](../../31_jalium-adapter/01_surface-and-host/index.md).

## What `-n`, `-ns` and `-o` do

- `-n` sets the class name and the file name. `sourceName: "TemplateClass"` is the substitution anchor, so it also rewrites `x:Class` and every reference to the class.
- `-ns` sets `TemplateNamespace` in every generated file. All seven must match.
- `-o` is the output folder. `preferNameDirectory` is `false` on every item, so `-o Views` writes directly into `Views/` with no per-name subfolder.

**The default names are load-bearing.** The tree writes `NodeView`, `SlotView`, `LinkView`, `TemplateSelector` (or `CustomTemplateSelector`), `GridDecorator` and `MinimapOverlay` into its markup or component tree. If you pass a non-default `-n`, edit the tree's reference in the same change; nothing else reports the mismatch.

## Expected result

- `dotnet new` exits 0 for all seven commands.
- `Views/` contains the whole suite: 11 files for the markup packs, 14 for Razor.
- `dotnet build` exits 0. Generation succeeding alone proves nothing: `dotnet new` substitutes strings without understanding them.

If the build fails, read [Verification and complete script](../03_verification/index.md) before editing the generated files.
