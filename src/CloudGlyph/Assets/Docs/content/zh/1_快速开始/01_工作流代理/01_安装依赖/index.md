# 01 · 安装依赖

## 方案 A —— NuGet 包

agent 位于可选伴随包 `VeloxDev.Core.Extension`（版本 `10.0.0`）中，它会传递引入 AI 技术栈。

```xml
<ItemGroup>
    <PackageReference Include="VeloxDev.Core.Extension" Version="10.0.0" />
</ItemGroup>
```

```bash
dotnet add package VeloxDev.Core.Extension --version 10.0.0
```

**预期结果：** 命令以 `0` 退出，`VeloxDev.Core.Extension`（及其传递 AI 包）出现在项目包列表 / `project.assets.json` 中。此时无需任何源码改动 —— 仅该包即可编译通过。

## 方案 B —— 项目引用（本仓库自身）

在本仓库内，每个 demo 与测试都直接引用源码项目，这也是让 Debug 构建使用源码生成器而非发布版的途径：

```xml
<ItemGroup>
    <ProjectReference Include="..\..\..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj" />
</ItemGroup>
```

来源：`Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`。

本库自身的 `Description` 仍写着「60+ function-calling tools」，那是 README 低估的数字。当前源码中精确、可核验的数量是 **68 个内置工具**，覆盖十个 `WorkflowToolCategory` 分组 —— 其中 66 个无条件注册，另加仅在配置了处理器时才注册的至多两个 `Interaction` 工具 —— 而 `ResetToolCallLimit` 始终在其之上追加。

## 你会用到的命名空间

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.AI` | 特性与反射辅助、`AgentLanguages`、`AgentObjectToolkit`、`AgentEmbeddedResources`、`AgentTelemetryExtensions`、事件参数与通知接口 |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope`、`AgentEx.AsAgentScope`、`WorkflowStateTracker`、`WorkflowAgentContextProvider`、`AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`、`WorkflowToolCategory`、`CommandInvoker`、`ComponentPatcher`、`TypeIntrospector` |
| `VeloxDev.AI.MCP` | `McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpServerStatus`、`McpSelfServiceLevel`、状态视图模型、`McpAgentToolkit` |
| `VeloxDev.AI.Skills` | `SkillScope`、`SkillAgentToolkit`、`SkillDescriptor`、`SkillState`、`SkillSourceKind`、`ISkillSource`、状态视图模型 |
| `VeloxDev.AI.SubAgents` | `SubAgentScope`、`SubAgentAgentToolkit`、`SubAgentAgentContextProvider`、`SubAgentState`/`SubAgentSummary`、树视图模型 |
| `VeloxDev.AI.Pipelines` | `AgentPipeline`、`AgentEvent`（及其子类）、`AgentTranscript`、`AgentTranscriptEntry`、`ToolPipeline`、`AgentPipelineAgent` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`、`AgentMemberViewModel` 及四个具体成员 |

要点：**`VeloxDev.AI` 是由 `VeloxDev.Core`（特性/反射）与 `VeloxDev.Core.Extension`（其余全部）共用的单一命名空间。** `VeloxDev.Core.Extension` 下的 `Agent/` 文件夹是实现细节；它声明的公开类型位于上述命名空间，而非某个 `VeloxDev.Core.Extension` 命名空间。

**预期结果：** 一个添加了 `using VeloxDev.AI.Workflow;` 的文件可以编译。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。包 id/版本与依赖版本读自 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`；未从本页执行 `dotnet add package` / 构建。
