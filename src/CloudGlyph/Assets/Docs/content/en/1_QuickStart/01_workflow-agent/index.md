# Workflow Agent — Quick Start

The **workflow-agent** feature is the AI control layer of VeloxDev. It turns a running workflow tree (an `IWorkflowTreeViewModel`, the same object the Workflow System Quick Start builds) into a surface an LLM can drive through function-calling tools:

- `tree.AsAgentScope()` returns a fluent `WorkflowAgentScope` builder. It collects prompt language, output language, type discovery, tool-call budgets, host-policy gates, interaction safety, callbacks and custom tools.
- `scope.ProvideProgressiveContextPrompt()` produces the system prompt (progressive disclosure keeps it small); `scope.ProvideAllContexts()` produces the full self-contained variant. Both automatically embed the bilingual prompt documents under `Resources/Workflow/{en,zh}` (`References`, `Skills`, `Safety`), so the agent learns the framework's rules from the same docs it reads.
- `scope.ProvideTools()` returns the `WorkflowAgentToolkit` tool set: 60 built-in `AITool`s (up to 62 with interaction tools), grouped by `WorkflowToolCategory` — Query, State, Mutation, Execution, Command, Graph, Layout, Analytics, Composite, Interaction.
- Execution is exposed at **three levels**, each with a run tool and a compile-only plan tool:
  - **Node level** — `ExecuteNode` / `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode` (drive one node's `ReceiveCommand` / broadcast commands, not compiled).
  - **Chain level (Root)** — `RunCompiledWorkflow(nodeIndex, seed?)` runs a compiled forward chain; `CompileWorkflow(nodeIndex)` only compiles the plan.
  - **Result level (Terminal)** — `GetNodeResult(nodeIndex, seed?)` computes one node's value from its ancestor cone; `CompileNodeResult(nodeIndex)` only compiles the cone.
  - Compile/run rest on `CompilerViewModel.CompileAsync(component, CompileRole.Root | CompileRole.Terminal)` plus `RuntimeEngine` (namespaces `VeloxDev.Core.WorkflowSystem.CompilerEx`) — the current engine; there is no `CompilerEngine` / `CompileToAsync` anymore.
- `WorkflowStateTracker` keeps JSON snapshots of the tree and reports `addedNodes/removedNodes/modifiedNodes` diffs so the agent observes change with minimal context.
- MCP support (`VeloxDev.AI.MCP`): `McpScope` loads Model Context Protocol servers (`McpServerRunMode.Npx`, `Http`, and more) and merges their tools into each conversation; `McpAgentToolkit` exposes host pre-registered servers to the agent as list/load/unload/describe tools.
- The reflection utilities in `VeloxDev.AI` (`AgentContextAttribute`, `AgentLanguages`, `AgentContextReader`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, event-args types, `SlotSelectorsAttribute`) back the type registry and the tools.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages (they build toward the single runnable program on the last page):

- [00 Prerequisites](00_prerequisites/) — supported targets, SDK/runtime, services you must supply (tree, `IChatClient`, optional MCP runtime)
- [01 Install & Add Dependencies](01_install/) — add `VeloxDev.Core.Extension` and the transitive AI packages
- [02 Build the Agent Scope](02_build-the-scope/) — `AsAgentScope()` fluent surface: languages, auto-discovery, prompt providers, tool retrieval
- [03 Tool Budgets & Host-Policy Gates](03_tool-budgets-and-host-policy/) — interaction safety 0–3, tool-call budgets, node-execution and generic-command gates, UI thread & dirty tracking
- [04 Custom Tools & MCP](04_custom-tools-and-mcp/) — `WithTools` / `WithQueryTools`, loading MCP servers, host-registered servers via `McpAgentToolkit`
- [05 Run a Conversation](05_run-a-conversation/) — prompt + tools onto a chat client, session, per-conversation tool merge, reply & undo
- [06 Three Execution Models](06_three-execution-models/) — node-level, Root chain and Terminal result tools; compile-only plans; the compiler engine underneath
- [07 Terminal Result Semantics](07_terminal-result-semantics/) — `GetNodeResult` / `CompileNodeResult`: ancestor cones, real `BranchSegment` routing, the `targetReached` contract and recovery
- [08 Verify & Complete Code](08_verify-and-complete-code/) — coverage by demos & tests, the single-file runnable program, and the run declaration
