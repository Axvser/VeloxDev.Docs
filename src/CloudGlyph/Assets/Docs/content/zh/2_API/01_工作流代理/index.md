# 工作流代理 —— API 参考

**workflow-agent** 特性的公开 API：把一棵 workflow 树变成可由工具操控的 AI agent 的那些部件。它横跨 `VeloxDev.AI` 系列命名空间，外加入口点扩展。

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope` 流式构建器、`WorkflowStateTracker`、`WorkflowAgentContextProvider`、`AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`（**68** 个内置 `AITool`）、`WorkflowToolCategory`、`CommandInvoker`、`ComponentPatcher`、`TypeIntrospector` |
| `VeloxDev.AI` | 特性、`AgentLanguages`、反射工具、事件参数与通知契约、`AgentObjectToolkit`、`AgentEmbeddedResources`、`AgentClientExtensions`、`AgentTelemetryExtensions` |
| `VeloxDev.AI.MCP` | `McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpServerStatus`、`McpSelfServiceLevel`、MCP 状态视图模型、`McpAgentToolkit`、`McpAgentContextProvider` |
| `VeloxDev.AI.Skills` | `SkillScope`、`SkillAgentToolkit`、`SkillAgentContextProvider`、`ISkillSource` 及两个实现、描述符/状态模型 |
| `VeloxDev.AI.SubAgents` | `SubAgentScope`、`SubAgentAgentToolkit`、`SubAgentAgentContextProvider`、`SubAgentState`/`SubAgentSummary`/`SubAgentStatusViewModel`、树视图模型 |
| `VeloxDev.AI.Pipelines` | `AgentPipeline`、`AgentEvent` 层级、`ToolPipeline`、`TextPipeline`、`AgentTranscript` 及条目、`AgentPipelineAgent` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`、`AgentMemberViewModel` 及其四个具体行 |

**关于 `VeloxDev.AI`。** 它是由 `VeloxDev.Core`（特性与反射辅助）与 `VeloxDev.Core.Extension`（其余）共用的单一命名空间。`VeloxDev.Core.Extension` 下的 `Agent/` 文件夹是实现细节；它声明的公开类型位于上述命名空间。

文档中的每个类型/成员/签名都对照当前源码核验；并附源码路径。底层编译执行是 `VeloxDev.Core.WorkflowSystem.CompilerEx` 引擎（`CompilerViewModel.CompileAsync(node, CompileRole)` + `RuntimeEngine`），其完整 API 记录在 `workflow-system` 特性的 `02_compilerex` API 页。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/**`、`Src/Core/VeloxDev.Core.Test/AI/*`）+ **Demo**（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`）。凡行为由源码推断而非 Demo/Test 者，标注为 *inferred*。

## API —— 分区

- [workflow](00_workflow/index.md) —— `WorkflowAgentScope` 流式表面、`WorkflowStateTracker`、`WorkflowAgentContextProvider`、`AgentContextCollector`。
- [functions](01_functions/index.md) —— `WorkflowAgentToolkit`、`WorkflowToolCategory`，以及按类别的完整工具清单：[查询与状态](01_functions/00_查询与状态工具/index.md)、[变更](01_functions/01_变更工具/index.md)、[执行](01_functions/02_执行工具/index.md)、[命令/图/分析/交互](01_functions/03_命令图分析与交互工具/index.md)、[辅助类](01_functions/04_辅助类/index.md)。
- [mcp](02_mcp/index.md) —— `VeloxDev.AI.MCP`：`McpScope`、配置/运行模式/自助枚举、状态视图模型、`McpAgentToolkit`、`McpAgentContextProvider`。
- [ai](03_ai/index.md) —— `VeloxDev.AI` 通用工具：特性、`AgentLanguages`、反射读取/发现/调用器、事件参数与通知接口、`AgentObjectToolkit`、`AgentEmbeddedResources`、`AgentTelemetryExtensions`。
- [agentex](04_agentex/index.md) —— `AgentEx.AsAgentScope` 与 `AgentClientExtensions.AsAIAgent`。
- [subagents](05_子代理/index.md) —— `VeloxDev.AI.SubAgents`：子系统、工具包 + 提供器、状态/行、树。
- [skills](06_skills/index.md) —— `VeloxDev.AI.Skills`：`SkillScope`、`SkillAgentToolkit`、来源与描述符/状态模型。
- [pipelines](07_pipelines/index.md) —— `VeloxDev.AI.Pipelines`：管线、事件、工具闸门、对话记录。
- [dashboard](08_dashboard/index.md) —— `VeloxDev.AI.Dashboard`：仪表盘视图模型与成员行。
