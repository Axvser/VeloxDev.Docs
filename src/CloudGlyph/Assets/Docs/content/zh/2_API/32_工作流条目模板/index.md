# 工作流条目模板

七个 GUI 适配器各发布一个 `dotnet new` **条目模板包**。包不是类库，也不是 demo：它是一组文本条目，把你自己的工程所需的视图层生成进去，用你的命名空间和你的配色。

每个包都发同样的七个角色 —— 一个宿主（`tree`）加六个部件 —— 行为已经接好。七个包 × 七个角色 = **49 个短名**。

| 包 | 短名前缀 | 面向 |
| --- | --- | --- |
| `VeloxDev.WPF.Templates` | `wpf` | WPF |
| `VeloxDev.Avalonia.Templates` | `ava` | Avalonia 11 |
| `VeloxDev.WinUI.Templates` | `winui` | WinUI 3 / Windows App SDK |
| `VeloxDev.MAUI.Templates` | `maui` | .NET MAUI |
| `VeloxDev.WinForms.Templates` | `winforms` | Windows Forms over Easel |
| `VeloxDev.Razor.Templates` | `razor` | Blazor / Razor |
| `VeloxDev.Jalium.Templates` | `jalium` | Jalium |

## 类型组

1. [包与角色](00_包与角色/index.md) —— 包元数据、七个角色、条目标识与文件数。
2. [短名称](01_短名称/index.md) —— 完整 49 名矩阵与每个平台的标识模式。
3. [生成选项](02_生成选项/index.md) —— `-n`、`-ns`、`-o`、每个样式符号及其别名、惰性值与默认值。
4. [生成文件](03_生成文件/index.md) —— 每个角色产出什么、已接好的行为、构建门槛。

## 包不提供什么

- **不提供 ViewModel。** 树、节点、插槽、连线 ViewModel，节点类型与 helper 都是你的。
- **不提供宿主外壳。** `App`、`Program`、`MainWindow` / `MainPage` / `MainForm` 来自 GUI 工程。
- **不提供连线菜单条目。** 树声明并接好菜单，但条目是空的。
- **不提供调试 HUD。** demo 里的 `InfoOverlay` 是宿主诊断，不是模板条目。

`* Trimmed` demo 是生成角色的最小调用序列镜像，不是 publish-trim 或 AOT 验证。
