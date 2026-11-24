# 前置条件

WPF 适配器就是一个普通的 WPF 类库。项目声明了四个目标框架，选哪个决定所需的 SDK。

## 支持的目标

来源：`Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`。

| 属性 | 声明的值 |
|---|---|
| `TargetFrameworks` | `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows` |
| `UseWPF` | `true` |
| `VeloxDev.Core` 依赖 | `12.3.0` |
| 包版本 | `12.3.0` |

裁剪版 demo 目标是 `net10.0-windows`；那是本页的**测过**配置，不是最低要求。`net8.0-windows` 工程受包支持，需要 .NET SDK 8.0 或更高。

## 工具

- **.NET SDK 8.0 或更高**，用于 `net8.0-windows`。.NET Framework 目标需要 C# 10 以上（`LangVersion latest`），因为生成的 ViewModel 用了区间/索引语法。
- **Windows** —— WPF 没有其他宿主。
- 不需要数据库、服务、API 密钥或网络。

## 添加包

```powershell
dotnet add package VeloxDev.WPF --version 12.3.0
```

**预期结果：** 命令退出码为 `0`，项目文件出现 `VeloxDev.WPF`，`VeloxDev.Core` 被传递还原。

包把 Core 生成器作为分析器依赖带上，所以下一页的 `[WorkflowBuilder.*]` 与 `[VeloxProperty]` 会生成 `InitializeWorkflow()`、`CreateNodeCommand`、`Helper`、`Nodes`、`Links` 以及属性变更钩子，不需要第二个包引用。

## 检查目标

```powershell
dotnet --list-sdks
```

**预期结果：** 至少有一个 `8.0.*`（或更高）条目。在 `net8.0-windows` 工程里，写入任何工作流类型之前 `dotnet build` 就能成功。
