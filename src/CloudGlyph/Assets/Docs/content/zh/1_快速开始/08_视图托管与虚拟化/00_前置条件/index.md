# 前置条件

这个功能的示例是 WPF。Avalonia 闭合同一组角色；它的池模板选择器是 `IDataTemplate`，而不是 WPF 的 `DataTemplateSelector`。

## 支持的目标

| 包 | 目标框架 |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`、`net5.0-windows`、`netcoreapp3.0`、`net8.0-windows` |
| `VeloxDev.Avalonia`（替代） | `netstandard2.0`、`net6.0`、`net8.0` |

示例目标为 `net8.0-windows`。示例工程目标为 `net10.0-windows` / `net10.0`，那是经过测试的配置，不是最低要求。

## 工具链

- .NET SDK 8.0+。
- WPF 需要 Windows。
- NuGet。

不需要外部服务。

## 添加包

```powershell
dotnet new wpf -n WorkflowPoolDemo
cd WorkflowPoolDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` 带入 `VeloxDev.Core`。生成器是分析器；NuGet 引用 Core 会带上它。`ProjectReference` 不会，所以该工程要把它作为分析器引用。示例显式安装生成器包，是为了构建期 Roslyn 检查。

## 可运行参考

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

WPF 镜像为 `Examples/Workflow/WPF Trimmed/Demo/Demo.csproj`。两者的生成器引用都来自 `Examples/Workflow/Directory.Build.props`。

## 预期结果

- `dotnet build` 退出码 0。
- XAML 中能解析 `VeloxDev.WorkflowSystem.AttachedBehaviors.ViewPool`。
- `[WorkflowBuilder.Tree<...>]` 分部类能编译，并暴露 `InitializeWorkflow()`。

如果找不到 `InitializeWorkflow`，缺的是生成器引用；如果找不到 `ViewPool`，缺的是适配器包。
