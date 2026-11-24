# 前置条件

## 支持的目标

来源：`Src/Adapters/VeloxDev.Avalonia/VeloxDev.Avalonia.csproj`。

| 属性 | 声明的值 |
|---|---|
| `TargetFrameworks` | `netstandard2.0;net6.0;net8.0` |
| `AvaloniaVersion` | `11.1.0` |
| `AvaloniaUseCompiledBindingsByDefault` | `true` |
| `VeloxDev.Core` 依赖 | `12.3.0` |
| 包版本 | `12.3.0` |

适配器基于 Avalonia 11.1.0 构建，随仓库发布的 demo 跑在 12.x 线上。本页跟随的是 `net8.0` 应用。

## 工具

- **.NET SDK 8.0 或更高**，用于 `net8.0`。
- **桌面操作系统** —— 完整代码使用 `Avalonia.Desktop` 与 `IClassicDesktopStyleApplicationLifetime`。
- 不需要数据库、服务、API 密钥或网络。

## 添加包

```powershell
dotnet add package VeloxDev.Avalonia --version 12.3.0
dotnet add package Avalonia.Desktop --version 11.1.0
dotnet add package Avalonia.Themes.Fluent --version 11.1.0
```

**预期结果：** 三条命令都退出 `0`；项目文件列出 `VeloxDev.Avalonia`、`Avalonia.Desktop` 与 `Avalonia.Themes.Fluent`，`VeloxDev.Core` 被传递还原。

Core 生成器作为包的分析器依赖随行，所以 `[WorkflowBuilder.*]` 与 `[VeloxProperty]` 会生成 `InitializeWorkflow()` 与标准命令，不需要额外引用。

## 工程设置

```xml
<PropertyGroup>
  <OutputType>WinExe</OutputType>
  <TargetFramework>net8.0</TargetFramework>
  <AvaloniaUseCompiledBindingsByDefault>true</AvaloniaUseCompiledBindingsByDefault>
  <Nullable>enable</Nullable>
  <LangVersion>latest</LangVersion>
</PropertyGroup>
```

**预期结果：** 写入任何工作流类型之前 `dotnet build` 就能成功。编译绑定打开后，缺少 `x:DataType` 的绑定作用域会报 `AVLN2100`，而不是静默返回空值。
