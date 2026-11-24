# 前置条件

小地图示例是 WPF。Avalonia 覆盖层来自同一条 Core 管线，属性名也相同（通过 `AvaloniaProperty`）。

## 支持的目标

| 包 | 目标框架 |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`、`net5.0-windows`、`netcoreapp3.0`、`net8.0-windows` |
| `VeloxDev.Avalonia`（替代） | `netstandard2.0`、`net6.0`、`net8.0` |

示例目标为 `net8.0-windows`。示例工程运行在 `net10.0-windows` / `net10.0`。

## 工具链

- .NET SDK 8.0+。
- WPF 需要 Windows。
- NuGet。

不需要服务。

## 添加包

```powershell
dotnet new wpf -n WorkflowMinimapDemo
cd WorkflowMinimapDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` 带入 `VeloxDev.Core`。示例声明了 `[WorkflowBuilder.*]` 与 `[VeloxProperty]`；NuGet 引用 Core 会带上分析器，显式安装生成器包是为了构建期 Roslyn 检查。

## 可运行参考

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

小地图出现在画布右上角。用资源管理器里的勾选框开关它。WPF 完整工作台（`Examples/Workflow/WPF/Demo`）有同一个覆盖层，开关绑到 `IsMinimapVisible`。

## 预期结果

- `dotnet build` 退出码 0。
- XAML 中能解析 `VeloxDev.WorkflowSystem.AttachedBehaviors.WorkflowMinimapOverlay`。
- 示例在画布上方显示小地图。

如果找不到类型，缺的是适配器包。如果覆盖层空白，表面行为没有解析到 `MinimapOverlayName` 或 `ScrollViewerName`。
