# 包与角色

七个包共享同样的打包形态与角色集合。差异只在标识中的平台段、短名前缀、标记扩展与生成文件数。

## 包元数据

| 包 | 版本 | PackageType | TargetFramework | 角色条目 | 每套生成文件 |
| --- | --- | --- | --- | --- | --- |
| `VeloxDev.WPF.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.Avalonia.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.WinUI.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.MAUI.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.WinForms.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 11 |
| `VeloxDev.Razor.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 14 |
| `VeloxDev.Jalium.Templates` | `12.0.0` | `Template` | `netstandard2.0` | 7 | 14 |

包不编译 C#，也不引用适配器。内容就是七个条目目录加上各自的 `.template.config/template.json` 与 `.template.config/dotnetcli.host.json`。生成文件确实会引用对应适配器（`assembly=VeloxDev.<GUI>` 或组件命名空间）与 `VeloxDev.WorkflowSystem`，所以工程里必须安装那个适配器包。

## 七个角色

| 角色 | 条目目录 | 标识后缀 | 默认类名 | 短名后缀 | 产出 |
| --- | --- | --- | --- | --- | --- |
| tree | `workflow-tree-view` | `WorkflowTreeView` | `TreeView` | `-tree` | 标记对 |
| node | `workflow-node-view` | `WorkflowNodeView` | `NodeView` | `-node` | 标记对 |
| slot | `workflow-slot-view` | `WorkflowSlotView` | `SlotView` | `-slot` | 标记对 |
| link | `workflow-link-view` | `WorkflowLinkView` | `LinkView` | `-link` | 标记对 |
| selector | `workflow-template-selector` | `WorkflowTemplateSelector` | `TemplateSelector`（WinForms 为 `CustomTemplateSelector`） | `-selector` | `.cs`（Razor：对） |
| decorator | `workflow-grid-decorator` | `WorkflowGridDecorator` | `GridDecorator` | `-decorator` | `.cs`（Razor：对） |
| minimap | `workflow-minimap-overlay` | `WorkflowMinimapOverlay` | `MinimapOverlay` | `-minimap` | `.cs`（Razor：对） |

标识是 `VeloxDev.<Platform>.Workflow<Role>`，例如 `VeloxDev.WinForms.WorkflowTreeView`。平台段是 `WPF`、`Avalonia`、`WinUI`、`MAUI`、`WinForms`、`Razor` 或 `Jalium`。

## 一套的形态

- **标记包**（WPF、Avalonia、WinUI、MAUI、WinForms、Jalium）：四对标记 + 代码隐藏（`tree`、`node`、`slot`、`link`）与三个独立 `.cs`（`selector`、`decorator`、`minimap`）。
- **Razor：** 七个角色都是 `.razor` + `.razor.cs` 对。

## 备注

- 七个条目必须共用一个命名空间。树按默认类名解析选择器、装饰器、小地图与节点/连线模板；拆到多个命名空间会得到一个找不到兄弟的构建。
- 默认名是承重的。传了非默认 `-n`，必须在同一次改动里改树中的引用。
- 这里的包版本是仓库自身的版本；消费工程应安装最新发布版。
