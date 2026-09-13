# 平台适配器 — 安装与引入依赖

为你要落地的 GUI 框架安装**模板包**并添加**适配器包**。本快速开始使用 WPF；其它平台把各自的包名/模板包换成特性概览表格里的对应项即可。

## 1. 安装模板包

```powershell
dotnet new install VeloxDev.WPF.Templates
```

如果你改为从本仓库构建模板包，则先 `dotnet pack` 对应工程，再安装产出的 `.nupkg`：

```powershell
dotnet pack Src/Templates/VeloxDev.WPF.Templates
dotnet new install Src/Templates/VeloxDev.WPF.Templates/bin/Debug/VeloxDev.WPF.Templates.9.0.0.nupkg
```

目标框架的模板包是适配器包的同级：`VeloxDev.{Platform}.Templates`，其项模板统一命名成 `{前缀}-v-*`（`wpf-v-*`、`winforms-v-*`、`ava-v-*`、`winui-v-*`、`maui-v-*`、`razor-v-*`、`jalium-v-*`）。网格装饰层项在所有平台都叫 `{前缀}-v-decorator`。

**预期结果：** `dotnet new list wpf-v` 会列出七个 `wpf-v-*` 项模板（在 `dotnet new list` 里也以 `VeloxDev.WPF.Workflow*` 身份出现）。

## 2. 引用适配器包

创建或打开 GUI 工程，然后添加匹配的包：

```powershell
dotnet new wpf -n WorkflowDemo -f net9.0
cd WorkflowDemo
dotnet add package VeloxDev.WPF
```

另外六个同级包用同样的方式添加（`VeloxDev.WinForms`、`VeloxDev.Avalonia`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.Razor`、`VeloxDev.Jalium`）。它们都包引用 `VeloxDev.Core`，会传递带入工作流引擎。在仓库内开发时改用对适配器的工程引用（仓库内演示就是这么做的，例如 `Examples/Workflow/WPF/Demo/Demo.csproj` 引用了 `Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`）。

**预期结果：** `.csproj` 增加 `<PackageReference Include="VeloxDev.WPF" Version="9.0.0" />`（或工程引用），`dotnet build` 通过——此时 XAML 与代码都能解析到 `VeloxDev.WorkflowSystem.AttachedBehaviors` 命名空间。

## 3. 全部包一览

| 适配器包 | 工作流引擎包 | 模板包 |
|---|---|---|
| `VeloxDev.WPF` | `VeloxDev.Core` | `VeloxDev.WPF.Templates` |
| `VeloxDev.WinForms` | `VeloxDev.Core` | `VeloxDev.WinForms.Templates` |
| `VeloxDev.Avalonia` | `VeloxDev.Core` | `VeloxDev.Avalonia.Templates` |
| `VeloxDev.WinUI` | `VeloxDev.Core` | `VeloxDev.WinUI.Templates` |
| `VeloxDev.MAUI` | `VeloxDev.Core` | `VeloxDev.MAUI.Templates` |
| `VeloxDev.Razor` | `VeloxDev.Core` | `VeloxDev.Razor.Templates` |
| `VeloxDev.Jalium` | `VeloxDev.Core` | `VeloxDev.Jalium.Templates` |
