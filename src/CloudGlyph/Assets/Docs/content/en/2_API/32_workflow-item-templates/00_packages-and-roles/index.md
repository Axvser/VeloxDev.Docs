# Packages and roles

All seven packs share the same packaging shape and role set. The differences are the platform segment in the identity, the prefix in the short name, the markup extension and the generated file count.

## Package metadata

| Package | Version | PackageType | TargetFramework | Role items | Generated files per suite |
| --- | --- | --- | --- | --- | --- |
| `VeloxDev.WPF.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.Avalonia.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.WinUI.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.MAUI.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.WinForms.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.Razor.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 14 |
| `VeloxDev.Jalium.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 14 |

A pack compiles no C# and references no adapter. Its content is the seven item directories plus their `.template.config/template.json` and `.template.config/dotnetcli.host.json`. The generated files do reference the matching adapter (`assembly=VeloxDev.<GUI>` or component namespaces) and `VeloxDev.WorkflowSystem`, so that adapter package must be installed in the project.

## The seven roles

| Role | Item directory | Identity suffix | Default class name | Short-name suffix | Output |
| --- | --- | --- | --- | --- | --- |
| tree | `workflow-tree-view` | `WorkflowTreeView` | `TreeView` | `-tree` | markup pair |
| node | `workflow-node-view` | `WorkflowNodeView` | `NodeView` | `-node` | markup pair |
| slot | `workflow-slot-view` | `WorkflowSlotView` | `SlotView` | `-slot` | markup pair |
| link | `workflow-link-view` | `WorkflowLinkView` | `LinkView` | `-link` | markup pair |
| selector | `workflow-template-selector` | `WorkflowTemplateSelector` | `TemplateSelector` (`CustomTemplateSelector` on WinForms) | `-selector` | `.cs` (Razor: pair) |
| decorator | `workflow-grid-decorator` | `WorkflowGridDecorator` | `GridDecorator` | `-decorator` | `.cs` (Razor: pair) |
| minimap | `workflow-minimap-overlay` | `WorkflowMinimapOverlay` | `MinimapOverlay` | `-minimap` | `.cs` (Razor: pair) |

The identity is `VeloxDev.<Platform>.Workflow<Role>`, for example `VeloxDev.WinForms.WorkflowTreeView`. The platform segment is `WPF`, `Avalonia`, `WinUI`, `MAUI`, `WinForms`, `Razor` or `Jalium`.

## Suite shape

- **Markup packs** (WPF, Avalonia, WinUI, MAUI, WinForms, Jalium): four markup + code-behind pairs (`tree`, `node`, `slot`, `link`) and three standalone `.cs` files (`selector`, `decorator`, `minimap`).
- **Razor:** all seven roles are `.razor` + `.razor.cs` pairs.

## Notes

- All seven items must share one namespace. The tree resolves its selector, decorator, minimap and node/link templates by their default class names; splitting them across namespaces produces a build that cannot find its siblings.
- The default names are load-bearing. A non-default `-n` requires editing the tree's reference in the same change.
- The pack version printed here is the repository's own; install the latest published version in a consuming project.
