# Short names

Every short name is `{prefix}-v-{suffix}`. The seven prefixes and seven role suffixes give the full 49-name matrix.

## The 49 short names

| Role | WPF | Avalonia | WinUI | MAUI | WinForms | Razor | Jalium |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tree | `wpf-v-tree` | `ava-v-tree` | `winui-v-tree` | `maui-v-tree` | `winforms-v-tree` | `razor-v-tree` | `jalium-v-tree` |
| node | `wpf-v-node` | `ava-v-node` | `winui-v-node` | `maui-v-node` | `winforms-v-node` | `razor-v-node` | `jalium-v-node` |
| slot | `wpf-v-slot` | `ava-v-slot` | `winui-v-slot` | `maui-v-slot` | `winforms-v-slot` | `razor-v-slot` | `jalium-v-slot` |
| link | `wpf-v-link` | `ava-v-link` | `winui-v-link` | `maui-v-link` | `winforms-v-link` | `razor-v-link` | `jalium-v-link` |
| selector | `wpf-v-selector` | `ava-v-selector` | `winui-v-selector` | `maui-v-selector` | `winforms-v-selector` | `razor-v-selector` | `jalium-v-selector` |
| decorator | `wpf-v-decorator` | `ava-v-decorator` | `winui-v-decorator` | `maui-v-decorator` | `winforms-v-decorator` | `razor-v-decorator` | `jalium-v-decorator` |
| minimap | `wpf-v-minimap` | `ava-v-minimap` | `winui-v-minimap` | `maui-v-minimap` | `winforms-v-minimap` | `razor-v-minimap` | `jalium-v-minimap` |

The suffix is `-decorator`, not `-grid`.

## Identity per platform

| Prefix | Pack | Identity segment | Example identity |
| --- | --- | --- | --- |
| `wpf` | `VeloxDev.WPF.Templates` | `VeloxDev.WPF` | `VeloxDev.WPF.WorkflowNodeView` |
| `ava` | `VeloxDev.Avalonia.Templates` | `VeloxDev.Avalonia` | `VeloxDev.Avalonia.WorkflowNodeView` |
| `winui` | `VeloxDev.WinUI.Templates` | `VeloxDev.WinUI` | `VeloxDev.WinUI.WorkflowNodeView` |
| `maui` | `VeloxDev.MAUI.Templates` | `VeloxDev.MAUI` | `VeloxDev.MAUI.WorkflowNodeView` |
| `winforms` | `VeloxDev.WinForms.Templates` | `VeloxDev.WinForms` | `VeloxDev.WinForms.WorkflowNodeView` |
| `razor` | `VeloxDev.Razor.Templates` | `VeloxDev.Razor` | `VeloxDev.Razor.WorkflowNodeView` |
| `jalium` | `VeloxDev.Jalium.Templates` | `VeloxDev.Jalium` | `VeloxDev.Jalium.WorkflowNodeView` |

The remaining roles substitute `NodeView` with `TreeView`, `SlotView`, `LinkView`, `TemplateSelector`, `GridDecorator` or `MinimapOverlay`.

## Verifying the registration

```powershell
dotnet new list winforms-v
```

**Expected result:** seven rows whose short names are exactly the WinForms column above. The same command works with any other prefix.

### Notes

- `dotnet new list {prefix}-v` filters by the shared `-v` segment; the matrix is the complete set, not a partial listing.
- A folder-mounted pack and a NuGet pack with the same short name make resolution ambiguous. `dotnet new install` exits non-zero on a duplicate; uninstall first.
