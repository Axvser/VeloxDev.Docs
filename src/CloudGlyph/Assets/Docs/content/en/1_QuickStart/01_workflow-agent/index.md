# Workflow Agent — Quick Start

The **workflow-agent** feature is the AI control layer of VeloxDev. It turns a live workflow tree (an `IWorkflowTreeViewModel`, the same object the Workflow System Quick Start builds) into a surface an LLM can drive through function-calling tools.

- `tree.AsAgentScope()` returns a fluent `WorkflowAgentScope` builder. It collects prompt language, output language, type discovery, tool-call budgets, host-policy gates, interaction safety, callbacks and custom tools.
- `scope.ProvideProgressiveContextPrompt()` produces the compact system prompt; `scope.ProvideAllContexts()` produces the full self-contained variant. Both embed the bilingual prompt documents under `Resources/Workflow/{en,zh}` (`References`, `Skills`, `Safety`).
- `scope.CreateContextProviders()` returns the per-invocation providers. The **`WorkflowAgentContextProvider` is the sole source of tools and instructions** on every turn, so attaching, switching off or loading something reaches the model on the next turn without rebuilding the agent.
- The default tool set is **68 built-in `AITool`s**, grouped by `WorkflowToolCategory` — Query (20), State (3), Mutation (23), Execution (12), Command (2), Graph (5), Layout (reserved), Analytics (1), Composite (reserved), Interaction (up to 2, only with a handler and safety level > 0), plus one always-present budget tool (`ResetToolCallLimit`).
- Execution is exposed at **three levels**, each with a run tool and a compile-only plan tool:
  - **Node level** — `ExecuteNode` / `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode` (one node's `ReceiveCommand` / broadcast commands, not compiled).
  - **Chain level (Root)** — `RunCompiledWorkflow(nodeIndex, seed?)` runs a compiled forward chain; `CompileWorkflow(nodeIndex)` only compiles the plan.
  - **Result level (Terminal)** — `GetNodeResult(nodeIndex, seed?)` computes one node's value from its ancestor cone; `CompileNodeResult(nodeIndex)` only compiles the cone.
  - A **run-handle family** starts the same compiled chain in the background and returns a handle: `StartCompiledWorkflow` / `ContinueCompiledWorkflow` → poll `GetCompiledRunStatus` → `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`.
- `WorkflowStateTracker` keeps JSON snapshots of the tree and reports added/removed/modified nodes and links so the agent observes change with minimal context.
- Four subsystems attach with one `With*` call each and contribute their own tools and prompt text per turn: **MCP** (`McpScope` / `McpAgentToolkit`), **Skills** (`SkillScope` / `SkillAgentToolkit`), **Sub-agents** (`SubAgentScope` / `SubAgentAgentToolkit`), and the **Pipeline/Transcript** observability chain (`AgentPipeline`, `AgentTranscript`, `AgentDashboardViewModel`).
- The reflection utilities in `VeloxDev.AI` (`AgentContextAttribute`, `AgentLanguages`, `AgentContextReader`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, event-args types, `SlotSelectorsAttribute`) back the type registry and the tools.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages (they build toward the single runnable program on the last page):

| Step | Page | What it does |
|---|---|---|
| 00 | [Prerequisites](00_prerequisites/index.md) | supported targets, SDK/runtime, packages, services you must supply (tree, `IChatClient`, optional MCP runtime) |
| 01 | [Install & Add Dependencies](01_install/index.md) | add `VeloxDev.Core.Extension` and the transitive AI packages |
| 02 | [Build the Agent Scope](02_build-the-scope/index.md) | `AsAgentScope()` fluent surface: languages, auto-discovery, prompt providers, tool retrieval |
| 03 | [Tool Budgets & Host-Policy Gates](03_tool-budgets-and-host-policy/index.md) | interaction safety 0–3, the three call budgets and `ResetToolCallLimit`, node-execution / generic-command gates, tool switches, tool approval, UI thread & dirty tracking |
| 04 | [Custom Tools & MCP](04_custom-tools-and-mcp/index.md) | `WithTools` / `WithQueryTools`, `WithMcps`, the MCP management tools, self-service levels |
| 05 | [Run a Conversation](05_run-a-conversation/index.md) | context providers onto a chat client, session, the pipeline & transcript, reply |
| 06 | [Three Execution Models](06_three-execution-models/index.md) | node-level, Root chain and Terminal result tools; compile-only plans |
| 07 | [Terminal Result Semantics](07_terminal-result-semantics/index.md) | `GetNodeResult` / `CompileNodeResult`: ancestor cones, real routing, the `targetReached` contract and recovery |
| 08 | [Compiled Run Handles](08_compiled-run-handles/index.md) | `StartCompiledWorkflow` → `GetCompiledRunStatus` → `Pause`/`Resume`/`Stop`; handle retirement; the `RunsOnOurGate` guard |
| 09 | [Dispatch Sub-Agents](09_sub-agents/index.md) | `SubAgentScope.ForClient` + `WithSubAgents`, the five management tools, capability narrowing, the one-pot ledger, the tree panel |
| 10 | [Skills & Pipelines](10_skills-and-pipelines/index.md) | `WithSkills`, embedded vs file skills, the four skill tools; `AgentPipeline`, `AgentTranscript`, `WithTranscript` |
| 11 | [Dashboard & Status](11_dashboard-and-status/index.md) | `AgentDashboardViewModel` and the MCP / Skills / Sub-agent status view-models |
| 12 | [Verify & Complete Code](12_verify-and-complete-code/index.md) | coverage by demos & tests, the single-file runnable program, and the Run Declaration |

## Where this lives

- Root: `Src/Core/VeloxDev.Core.Extension/Agent/` (tree: `Workflow/`, `MCP/`, `Skills/`, `SubAgents/`, `Pipelines/`, `Dashboard/`).
- Reflection/attributes: `Src/Core/VeloxDev.Core/AI/`.
- Toolkit: `Agent/Workflow/Functions/WorkflowAgentToolkit.cs`; categories in `WorkflowToolCategory.cs`.
- Demo (primary evidence): `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` and the dialogs beside it.
- Tests: `Src/Core/VeloxDev.Core.Extension.Test/Agent/**` and `Src/Core/VeloxDev.Core.Test/AI/*`.
