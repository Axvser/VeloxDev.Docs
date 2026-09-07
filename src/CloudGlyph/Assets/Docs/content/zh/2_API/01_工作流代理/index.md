# 工作流代理 — API 参考

`workflow-agent` 功能的公开 API：把一棵工作流树变为可由 Agent 工具化操作的全部部件，覆盖四个命名空间外加入口扩展：

- `VeloxDev.AI.Workflow` — `AgentEx.AsAgentScope` → `WorkflowAgentScope`（流式配置、上下文提示词、能力闸门）、`WorkflowStateTracker`、`AgentContextCollector`。
- `VeloxDev.AI.Workflow.Functions` — `WorkflowAgentToolkit`（约 60 个 `AITool`）、`WorkflowToolCategory`，以及辅助类 `CommandInvoker`、`ComponentPatcher`、`TypeIntrospector`。
- `VeloxDev.AI.MCP` — `McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpServerStatus`、可绑定的状态视图模型与 `McpAgentToolkit`。
- `VeloxDev.AI` — 通用 AI 上下文/反射工具（`AgentContextAttribute`、`AgentContextReader`、`AgentCommandDiscoverer`、`AgentMethodInvoker`、`AgentPropertyAccessor`、`AgentTypeResolver`、`AgentLanguages`）、交互事件参数与通知契约，以及通用对象工具包 `AgentObjectToolkit`。

页面中出现的每个类型、成员与签名均已对照当前源码核实，并标注源码路径。底层编译执行为 `VeloxDev.Core.WorkflowSystem.CompilerEx` 引擎（`CompilerViewModel.CompileAsync(node, CompileRole)` + `RuntimeEngine`），其完整 API 见 `workflow-system` 功能的 `02_compilerex` API 页。

**证据：** **测试**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/**`、`Src/Core/VeloxDev.Core.Test/AI/*`）+ **Demo**（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`、`Examples/Workflow/WinForms/Demo/Form1.cs`）+ README。凡无 Demo/Test 直接证据、仅由源码推断的行为均标注 *推断所得*。

## API — 栏目

- [00_workflow](00_workflow/index.md) —— `VeloxDev.AI.Workflow` 核心：`WorkflowAgentScope` 流式构建器与内嵌 `SelectionResult`、`WorkflowStateTracker` 快照/差异、`AgentContextCollector` 上下文块。
- [01_functions](01_functions/index.md) —— `VeloxDev.AI.Workflow.Functions`：`WorkflowAgentToolkit`、`WorkflowToolCategory`、按类别的完整工具清单（Query / State / Mutation / Execution / Command / Graph / Analytics / Interaction），以及辅助类 `CommandInvoker` / `ComponentPatcher` / `TypeIntrospector`。
- [02_mcp](02_mcp/index.md) —— `VeloxDev.AI.MCP`：`McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpServerStatus`、状态视图模型、`McpAgentToolkit`。
- [03_ai](03_ai/index.md) —— `VeloxDev.AI` 通用工具：特性、`AgentLanguages`、反射读取器/发现器/调用器、事件参数与通知契约、`AgentObjectToolkit`、`AgentEmbeddedResources`。
- [04_agentex](04_agentex/index.md) —— `AgentEx.AsAgentScope` 入口点，以及宿主运行 Agent 时使用的 `chatClient.AsAIAgent(...)` 装配方式。
