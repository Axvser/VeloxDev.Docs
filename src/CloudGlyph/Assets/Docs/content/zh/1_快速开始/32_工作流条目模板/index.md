# 工作流条目模板

七个 GUI 适配器各发布一个 `dotnet new` **条目模板包**。包不是类库，也不是 demo：它是一组文本条目，把你自己的工程所需的视图层生成进去，用你的命名空间和你的配色。

每个包都发同样的七个角色 —— 一个宿主（`tree`）加六个部件 —— 行为已经接好。

| 包 | 短名前缀 | 面向 |
| --- | --- | --- |
| `VeloxDev.WPF.Templates` | `wpf` | WPF |
| `VeloxDev.Avalonia.Templates` | `ava` | Avalonia 11 |
| `VeloxDev.WinUI.Templates` | `winui` | WinUI 3 / Windows App SDK |
| `VeloxDev.MAUI.Templates` | `maui` | .NET MAUI |
| `VeloxDev.WinForms.Templates` | `winforms` | Windows Forms over Easel |
| `VeloxDev.Razor.Templates` | `razor` | Blazor / Razor |
| `VeloxDev.Jalium.Templates` | `jalium` | Jalium |

七个包 × 七个角色 = **49 个短名**，全部列在[生成一套视图](01_生成一套视图/index.md)。

| 角色 | 条目目录 | 默认类名 | 后缀 |
| --- | --- | --- | --- |
| tree | `workflow-tree-view` | `TreeView` | `-tree` |
| node | `workflow-node-view` | `NodeView` | `-node` |
| slot | `workflow-slot-view` | `SlotView` | `-slot` |
| link | `workflow-link-view` | `LinkView` | `-link` |
| selector | `workflow-template-selector` | `TemplateSelector`（WinForms 为 `CustomTemplateSelector`） | `-selector` |
| decorator | `workflow-grid-decorator` | `GridDecorator` | `-decorator` |
| minimap | `workflow-minimap-overlay` | `MinimapOverlay` | `-minimap` |

## 包不提供什么

- **不提供 ViewModel。** 树、节点、插槽、连线 ViewModel，节点类型与 helper 都是你的。
- **不提供宿主外壳。** `App`、`Program`、`MainWindow` / `MainPage` / `MainForm` 来自 GUI 工程。
- **不提供连线菜单条目。** 树声明并接好菜单，但条目是空的。
- **不提供调试 HUD。** demo 里的 `InfoOverlay` 是宿主诊断，不是模板条目。

## 按顺序阅读

1. [前置条件与安装](00_前置条件/index.md) —— SDK、对应适配器包、安装与卸载、单一命名空间。
2. [生成一套视图](01_生成一套视图/index.md) —— 完整 49 个短名与每个包的七条命令。
3. [定制生成的视图](02_定制/index.md) —— 样式参数、选择器、连线菜单、平台差异。
4. [验证与完整脚本](03_验证/index.md) —— 构建即检查、常见失败、完整生成脚本、运行声明。
