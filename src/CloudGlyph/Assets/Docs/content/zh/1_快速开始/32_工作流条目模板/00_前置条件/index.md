# 前置条件与安装

## 包是什么

每个包都是带 `<PackageType>Template</PackageType>` 与 `TargetFramework netstandard2.0` 的 NuGet 包。它不编译任何 C#，也不引用适配器：内容就是七个条目目录及各自的 `.template.config/template.json`。本仓库里七个包的版本都是 **12.0.0**。

生成出来的文件确实引用适配器 —— 标记类包通过 `assembly=VeloxDev.<GUI>`，Razor 通过组件命名空间 —— 以及 `VeloxDev.WorkflowSystem`，所以工程里必须装对应的适配器包。模板包每台机器装一次；适配器包按工程装。

## 要求

- 一个足够新的 .NET SDK 来运行 `dotnet new`。包本身是 `netstandard2.0`；*生成后的*工程决定它自己的 SDK 底线。
- 目标 GUI 的适配器包：`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor` 或 `VeloxDev.Jalium`。
- 对应 GUI 的 SDK 或工作负载：WinUI 与 MAUI 需要各自 workload，Razor 需要 ASP.NET Core 共享框架，Jalium 需要 .NET 10。
- 不需要数据库、服务或 API 密钥。

## 安装一个包

```powershell
dotnet new install VeloxDev.WinForms.Templates
dotnet add package VeloxDev.WinForms
```

把两个名字换成目标 GUI。两者都装**最新发布版**；不要把适配器钉在本仓库打印的版本上。

**预期结果：** `dotnet new list winforms-v` 列出七个短名。没有适配器包时生成仍会成功；失败要到构建才出现。

## 卸载 / 重装

同名短名的文件夹挂载包与 NuGet 包会让解析含糊，重复注册还会让 `dotnet new install` 以非零码退出。每个短名只保留一个注册：

```powershell
dotnet new uninstall VeloxDev.WinForms.Templates
dotnet new install VeloxDev.WinForms.Templates
```

## 一套模板共用一个命名空间

七个条目必须生成到同一个命名空间。树通过命名空间别名（Razor 是裸类型名）按默认类名解析选择器、装饰器、小地图与节点/连线模板。拆到两个命名空间会得到一个找不到兄弟的构建。

ViewModel 与宿主外壳不在生成范围内。最小的 ViewModel 集是 `Examples/Workflow/<GUI> Trimmed/Demo/ViewModels/Workflow/`（Razor 的 demo 目录名为 `Blazor Trimmed`）；对应的适配器快速开始展示了四个类：

- [WinForms 适配器](../../29_WinForms适配器/01_表面与宿主/index.md)
- [Razor 适配器](../../30_Razor适配器/01_表面与宿主/index.md)
- [Jalium 适配器](../../31_Jalium适配器/01_表面与宿主/index.md)
