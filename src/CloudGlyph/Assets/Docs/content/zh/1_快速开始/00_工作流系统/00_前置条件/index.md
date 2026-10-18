# 工作流系统 — 前置条件

- **支持的目标框架**（来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`）：
  `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0` —— 库本身可用于 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 与 .NET 8+。`VeloxDev.Core.Extension` 的目标框架是 `netstandard2.0` / `net8.0`。
- **SDK / 运行时：** 现代 .NET SDK。后续页面的组件声明使用**部分属性**（`[VeloxProperty] public partial QuickSlot InputSlot { get; set; }`），这是生成器消费的 C# 13 特性，因此 SDK 必须自带 Roslyn 4.12+（**.NET SDK 9.0+**；本指南的示例目标为 `net10.0`，与仓库的 Trimmed demo 生成方式及记录运行所用的 .NET SDK 10.0.401 一致）。
- **包管理器：** NuGet / `dotnet` CLI（`dotnet new`、`dotnet add reference`、`dotnet restore`）。
- **需要的服务：** 无 —— 核心引擎自包含、可无头运行。Python 只在运行 *demo 的* Python 工作节点时才需要（见「验证与完整代码」），本快速开始不需要。
- **仓库结构（本教程的事实基准）：**
  - 共享 demo 组件与会话构建器：`Examples/Workflow/Common/Lib/ViewModels/Workflow/`（`ControllerViewModel.cs`、`TimerNodeViewModel.cs`、`EnumSelectorNodeViewModel.cs`、`WorkflowDemoSession.cs`、`Helper/*`）。
  - 编译器 / 运行时引擎源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/`（`Compile/`、`Runtime/`）。
  - 编译器契约测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`。

**预期结果：** `dotnet --version` 返回 9.0.x 或更高，并且你能打开仓库的 `VeloxDev.sln`。
