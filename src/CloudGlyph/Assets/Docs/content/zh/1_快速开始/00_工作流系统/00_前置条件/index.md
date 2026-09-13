# 工作流系统 — 前置条件

本快速开始带你从零搭一个 .NET 控制台项目，复用真实 Demo（`Examples/Workflow/Common/Lib`）里的写法，把一张工作流图画出来并编译运行。

#### 1. 支持的 .NET 目标

取自已声明的目标框架（`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 的 `TargetFrameworks`）：

- `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`

即：可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。下表说明本指南选用的**被验证过**的运行配置（只是示例已验证的组合，不是最低要求）：

| 项 | 值 |
|---|---|
| 示例项目 TFM | `net9.0`（经 `netstandard2.0` 资产引用核心库） |
| .NET SDK | 10.0.400（本指南实测；≥ Roslyn 4.x 即可跑源码生成器） |

#### 2. SDK / 运行时

- 需要带 **Roslyn 4.x** 的 .NET SDK 才能执行 Roslyn 源码生成器（`VeloxDev.Core.Generator`），它随 `VeloxDev.Core` 传递依赖自动成为 Analyzer。
- 仓库内示例面向 `net9.0`；那是*被验证过*的配置，并非最低版本。

**预期结果：** 在命令行执行 `dotnet --list-sdks` 能看到 ≥ 9 的 SDK；`dotnet --list-runtimes` 能看到对应的 .NET 运行时。

#### 3. 包管理器

- NuGet / `dotnet` CLI（`dotnet new`、`dotnet add package`、`dotnet restore`）。

#### 4. 所需服务

- 无。核心引擎自包含，不依赖外部服务。本指南不启动任何 GUI。

**预期结果：** 无服务依赖；新建并构建一个空控制台项目即退出码 0。

> 若本地无法逐项核验上面的工具链，文末 [07 完整代码](../07_完整代码/index.md) 的运行声明会如实降级为 ⚠️。

## 下一步

准备好工具链后，进入 [01 安装 / 添加依赖](../01_安装/index.md)。
