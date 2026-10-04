# Workflow Agent — Patterns Overview

| Pattern | Where | Role |
|---|---|---|
| Builder | `WorkflowAgentScope` | Fluent `With*` configuration; every method returns the same scope and bumps `Version` on a real change. |
| Facade | `WorkflowAgentToolkit` | One 68-tool surface hides reflection, command dispatch and compact JSON. |
| Decorator | `TrackedAIFunction` (internal) | Wraps every `AIFunction` so each call is marshalled, gated, counted and reported. |
| Memento | `WorkflowStateTracker` | JSON snapshots + property-level diffs so the model sees change, not the whole state. |
| Command | The Mutation tools | Each dispatches exactly one `IWorkflow*ViewModel` command; Core owns undo/redo. |
| Adapter | `McpScope` / `McpAgentToolkit` | Local (stdio) and remote (HTTP) MCP servers exposed as `AITool`s. |
| Adapter | `SkillScope` / `SkillAgentToolkit` | Embedded and file Agent Skills exposed as four `AITool`s. |
| Strategy | `WorkflowToolCategory` | A `[Flags]` mask selects which tool groups are built. |
| Strategy | Interaction handlers | `WithInteractionSafety` level 0–3 picks the policy; the two handlers plug the behaviour. |
| Observer | `AgentPipeline` + the notifier interfaces | Run/tool events published to a stage chain; `ToolCalled` raised on the scope. |
| Chain of responsibility | `AgentPipeline` | `TextPipeline` → `ToolPipeline` → `AccountingStage`; a stage may drop an event for the stages after it. |
| Mediator (gate) | `ToolPipeline` | One shared policy per scope enforces budgets, switches and approval across every slice. |
| Narrowed view | sub-agent spawn / skill grant / MCP grant | A capability that carries its own reconfiguration is handed down as a *filtered view*, not a name list. |
| Composite ledger (chain) | `ToolCallLedger` | A child's allowance is a share of its parent's; `Spend` walks the chain so the root sees the whole tree. |
| Lazy cache (memoized render) | `WorkflowAgentContextProvider` | Renders per turn, reuses the previous render (and the very same `AIContext`) while nothing moved. |

## The two structural themes of the subsystem layer

1. **One gate, every slice.** Budgets, per-tool switches and tool approval live on one `ToolPipeline` instance per scope, handed to the MCP and skill providers as well as used by the built-ins. A switch therefore cannot be honoured on one path and ignored on another.

2. **Narrowing is intersection, always.** A spawn's tool list, skill set, MCP server set, budget caps, node-execution flag and dirty-marking mode are each intersected with what the parent actually holds, and whatever is dropped is reported back in the spawn's own result. The parent is the ceiling by construction.

> See the per-pattern sub-pages for diagrams and source references.
