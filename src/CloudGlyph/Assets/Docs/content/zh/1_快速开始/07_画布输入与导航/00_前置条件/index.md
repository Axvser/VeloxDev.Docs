# 前置条件

这个快速开始构建一个 WPF 宿主。Core 的契约与平台无关；Avalonia 适配器闭合同一组角色，但它的属性是 `AvaloniaProperty`，模板选择器是 `IDataTemplate`。

## 支持的目标

`VeloxDev.Core` 与 `VeloxDev.WPF` 在项目文件里声明了下列目标框架。新建宿主可以目标 `net8.0-windows`；示例工程目标为 `net10.0-windows`，那是一种经过测试的配置，不是最低要求。

| 包 | 目标框架 |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`、`net5.0-windows`、`netcoreapp3.0`、`net8.0-windows` |
| `VeloxDev.Avalonia`（替代） | `netstandard2.0`、`net6.0`、`net8.0` |

## 工具链

- **.NET SDK 8.0 或更新**，对应示例的 `net8.0-windows`。
- **Windows**，WPF 需要。
- 一个 NuGet 客户端（`dotnet` CLI 即可）。

不需要服务、数据库或 API 密钥。

## 添加包

```powershell
dotnet new wpf -n WorkflowSurfaceDemo
cd WorkflowSurfaceDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` 会带入 `VeloxDev.Core`。生成器是 Roslyn 分析器。NuGet 引用 Core 会带上它；`ProjectReference` 不会，所以通过工程引用声明 `[WorkflowBuilder.*]` 或 `[VeloxProperty]` 的工程要把它作为分析器引用。本树显式安装生成器包，是为了它的构建期 Roslyn 检查。包版本是 12.3.0；生成器要与 Core 保持同一版本。

如果你想直接运行仓库示例而不是新建工程：

```powershell
dotnet run --project "Examples/Workflow/WPF Trimmed/Demo/Demo.csproj"
```

那个工程已经通过 `Examples/Workflow/Directory.Build.props` 引用了适配器与生成器。

## 预期结果

- `dotnet build` 以退出码 0 结束。
- 工程文件里列出 `VeloxDev.WPF` 与 `VeloxDev.Core.Generator`。
- XAML 中能解析 `VeloxDev.WorkflowSystem.AttachedBehaviors` 命名空间。

如果缺生成器，`[WorkflowBuilder.Tree<...>]` 分部类会报「成员不存在」——这是常见症状，不是缺适配器引用。
