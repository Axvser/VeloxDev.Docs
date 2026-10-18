# 前置条件

## 支持的目标

整个 AOP 运行时都在 `#if NET` 内编译（`Src/Core/VeloxDev.Core/AspectOriented/*.cs`、`Interfaces/AspectOriented/IAspectOriented.cs`）。`VeloxDev.Core.csproj` 多目标 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`，其中只有 **`net5.0` 与 `net8.0` 资产**定义了 `NET`。

| 消费方 TFM | 是否可用 |
|---|---|
| `net5.0` 及以上（`net6.0`、`net7.0`、`net8.0`、`net9.0`、`net10.0`、`net*-windows`） | 可用 —— 取 `net5.0` 或 `net8.0` 资产 |
| `netcoreapp3.0` | 不可用 —— .NET Core 3.x 不定义 `NET` |
| `netstandard2.0`、`netframework4.6.1` | 不可用 —— 运行时类型不存在 |

`net9.0` 或 `net10.0` 工程会解析到包的 `net8.0` 资产，该资产以 `IsAotCompatible=true` 构建。代理本身是生成的 C#，因此裁剪与 NativeAOT 下没有运行时代码生成可失败。

## 工具链

- **.NET SDK 8.0 或更高。** 生成器程序集引用 `Microsoft.CodeAnalysis.CSharp` 4.8.0（`VeloxDev.Core.Generator.csproj`），即 .NET 8 SDK 与 Visual Studio 2022 17.8 自带的 Roslyn 版本。本指南用 SDK 10.0.401 验证。
- **C# 12 或更高。** 生成器要求 `LangVersion` 为 12（`latest`），低于此会报告 `VELOX_LANGVERSION001`。
- **NuGet / `dotnet` CLI。**

## 所需服务

无。AOP 是纯粹的 `VeloxDev.Core` + 生成器功能：不需要平台适配器、数据库或配置文件。

## 预期结果

```bash
dotnet --version
```

输出 `8.0.x` 或更高版本，`dotnet --list-sdks` 中能看到同一个 SDK。
