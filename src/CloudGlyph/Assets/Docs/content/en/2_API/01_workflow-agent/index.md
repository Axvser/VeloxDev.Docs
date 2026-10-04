# Workflow Agent — API Reference

Public API of the `workflow-agent` feature: the pieces that turn a workflow tree into a tool-operable AI agent. It spans the `VeloxDev.AI` family of namespaces plus the entry-point extensions.

| Namespace | Contents |
|---|---|
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope` fluent builder, `WorkflowStateTracker`, `WorkflowAgentContextProvider`, `AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit` (the **68** built-in `AITool`s), `WorkflowToolCategory`, `CommandInvoker`, `ComponentPatcher`, `TypeIntrospector` |
| `VeloxDev.AI` | attributes, `AgentLanguages`, the reflection utilities, event args + notifier contracts, `AgentObjectToolkit`, `AgentEmbeddedResources`, `AgentClientExtensions`, `AgentTelemetryExtensions` |
| `VeloxDev.AI.MCP` | `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpServerStatus`, `McpSelfServiceLevel`, the MCP status view-models, `McpAgentToolkit`, `McpAgentContextProvider` |
| `VeloxDev.AI.Skills` | `SkillScope`, `SkillAgentToolkit`, `SkillAgentContextProvider`, `ISkillSource` + its two implementations, the descriptor/state model |
| `VeloxDev.AI.SubAgents` | `SubAgentScope`, `SubAgentAgentToolkit`, `SubAgentAgentContextProvider`, `SubAgentState`/`SubAgentSummary`/`SubAgentStatusViewModel`, the tree view-models |
| `VeloxDev.AI.Pipelines` | `AgentPipeline`, the `AgentEvent` hierarchy, `ToolPipeline`, `TextPipeline`, `AgentTranscript` + entries, `AgentPipelineAgent` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`, `AgentMemberViewModel` + its four concrete rows |

**Note on `VeloxDev.AI`.** It is a single namespace shared by `VeloxDev.Core` (attributes and reflection helpers) and `VeloxDev.Core.Extension` (the rest). The `Agent/` folder under `VeloxDev.Core.Extension` is an implementation detail; the public types it declares live in the namespaces above.

Every documented type/member/signature is verified against the current source; source paths are cited. Underlying compiled execution is the `VeloxDev.Core.WorkflowSystem.CompilerEx` engine (`CompilerViewModel.CompileAsync(node, CompileRole)` + `RuntimeEngine`), whose full API is documented on the `workflow-system` feature's `02_compilerex` API page.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/**`, `Src/Core/VeloxDev.Core.Test/AI/*`) + **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`). Where a behavior is inferred from source rather than Demo/Test it is marked *inferred*.

## API — Sections

- [workflow](00_workflow/index.md) — `WorkflowAgentScope` fluent surface, `WorkflowStateTracker`, `WorkflowAgentContextProvider`, `AgentContextCollector`.
- [functions](01_functions/index.md) — `WorkflowAgentToolkit`, `WorkflowToolCategory`, and the full per-category tool inventory: [Query & State](01_functions/00_query-state-tools/index.md), [Mutation](01_functions/01_mutation-tools/index.md), [Execution](01_functions/02_execution-tools/index.md), [Command/Graph/Analytics/Interaction](01_functions/03_command-graph-analytics-interaction/index.md), and the [helper classes](01_functions/04_helpers/index.md).
- [mcp](02_mcp/index.md) — `VeloxDev.AI.MCP`: `McpScope`, the configuration/run-mode/self-service enums, the status view-models, `McpAgentToolkit`, `McpAgentContextProvider`.
- [ai](03_ai/index.md) — `VeloxDev.AI` generic utilities: attributes, `AgentLanguages`, reflection readers/discoverers/invokers, event args + notifier interfaces, `AgentObjectToolkit`, `AgentEmbeddedResources`, `AgentTelemetryExtensions`.
- [agentex](04_agentex/index.md) — `AgentEx.AsAgentScope` and `AgentClientExtensions.AsAIAgent`.
- [subagents](05_subagents/index.md) — `VeloxDev.AI.SubAgents`: the subsystem, toolkit + provider, state/rows, the tree.
- [skills](06_skills/index.md) — `VeloxDev.AI.Skills`: `SkillScope`, `SkillAgentToolkit`, the sources and descriptor/state model.
- [pipelines](07_pipelines/index.md) — `VeloxDev.AI.Pipelines`: the pipeline, events, tool gate, transcript.
- [dashboard](08_dashboard/index.md) — `VeloxDev.AI.Dashboard`: the dashboard view-model and member rows.
