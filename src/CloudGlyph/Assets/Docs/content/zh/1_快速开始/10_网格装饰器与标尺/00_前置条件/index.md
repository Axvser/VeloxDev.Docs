# 前置条件

示例是 WPF。Avalonia、WinUI、MAUI、WinForms、Razor、Jalium 包各自提供等价的装饰器条目；绘制 API 不同，契约相同。

## 支持的目标

| 包 | 目标框架 |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`、`net5.0-windows`、`netcoreapp3.0`、`net8.0-windows` |
| `VeloxDev.Avalonia`（替代） | `netstandard2.0`、`net6.0`、`net8.0` |

示例目标为 `net8.0-windows`；示例工程运行在 `net10.0-windows` / `net10.0`。

## 工具链

- .NET SDK 8.0+。
- WPF 需要 Windows。
- NuGet 与 `dotnet new` 模板引擎。

不需要服务。

## 添加包

```powershell
dotnet new wpf -n WorkflowGridDemo
cd WorkflowGridDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

## 生成装饰器（可选）

```powershell
dotnet new install VeloxDev.WPF.Templates
dotnet new wpf-v-decorator -n WorkflowGridDecorator -o Views/Workflow
```

生成的类实现 `IWorkflowGridDecorator`，暴露 `RulerThickness`、`GridSpacing`、`MajorLineEvery`、四个偏移与 `RulerBand`，并画出网格与标尺。这个功能的[验证](../03_验证/index.md)页上的示例是同一个类的精简版。

每台机器只需安装一次模板包。如果 `dotnet new wpf-v-decorator` 解析含糊，说明文件夹挂载的模板与包同名注册了；`dotnet new uninstall` 会列出已安装项，没有 PackageId 的那条就是文件夹挂载的。

## 可运行参考

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

WPF 镜像为 `Examples/Workflow/WPF Trimmed/Demo/Demo.csproj`；它的装饰器在 `Views/Workflow/WorkflowGridDecorator.cs`。

## 预期结果

- `dotnet build` 退出码 0。
- 能从 `VeloxDev.WorkflowSystem` 解析 `IWorkflowGridDecorator`。
- `dotnet new wpf-v-decorator` 生成一个 `.cs` 文件，类名是你给的。

如果模板命令不存在，模板包没装；如果类型编译不过，适配器包没装。
