# Workflow Agent — API Reference

Public API of the `workflow-agent` feature: the pieces that turn a workflow tree into a tool-operable AI agent. It spans four namespaces plus the entry-point extension:

- `VeloxDev.AI.Workflow` — `AgentEx.AsAgentScope` → `WorkflowAgentScope` (fluent configuration, context prompts, capability gates), `WorkflowStateTracker`, `AgentContextCollector`.
- `VeloxDev.AI.Workflow.Functions` — `WorkflowAgentToolkit` (the ~60 `AITool` set), `WorkflowToolCategory`, and the helper classes `CommandInvoker`, `ComponentPatcher`, `TypeIntrospector`.
- `VeloxDev.AI.MCP` — `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpServerStatus`, the bindable status view-models, and `McpAgentToolkit`.
- `VeloxDev.AI` — generic AI context/reflection utilities (`AgentContextAttribute`, `AgentContextReader`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, `AgentLanguages`), interaction event args + notifier contracts, and the generic object toolkit `AgentObjectToolkit`.

Every documented type/member/signature is verified against the current source; source paths are cited. Underlying compiled execution is the `VeloxDev.Core.WorkflowSystem.CompilerEx` engine (`CompilerViewModel.CompileAsync(node, CompileRole)` + `RuntimeEngine`), whose full API is documented on the `workflow-system` feature's `02_compilerex` API page.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/**`, `Src/Core/VeloxDev.Core.Test/AI/*`) + **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, `Examples/Workflow/WinForms/Demo/Form1.cs`) + README. Where a behavior is inferred from source rather than Demo/Test it is marked *inferred*.

## API — Sections

- [workflow](00_workflow/index.md) — `VeloxDev.AI.Workflow` core: `WorkflowAgentScope` fluent builder + nested `SelectionResult`, `WorkflowStateTracker` snapshots/diffs, `AgentContextCollector` context blocks.
- [functions](01_functions/index.md) — `VeloxDev.AI.Workflow.Functions`: `WorkflowAgentToolkit`, `WorkflowToolCategory`, the full per-category tool inventory (Query / State / Mutation / Execution / Command / Graph / Analytics / Interaction), and the helpers `CommandInvoker` / `ComponentPatcher` / `TypeIntrospector`.
- [mcp](02_mcp/index.md) — `VeloxDev.AI.MCP`: `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpServerStatus`, status view-models, `McpAgentToolkit`.
- [ai](03_ai/index.md) — `VeloxDev.AI` generic utilities: attributes, `AgentLanguages`, reflection readers/discoverers/invokers, event args + notifier interfaces, `AgentObjectToolkit`, `AgentEmbeddedResources`.
- [agentex](04_agentex/index.md) — `AgentEx.AsAgentScope` entry point and the `chatClient.AsAIAgent(...)` wiring the host uses to run the agent.
