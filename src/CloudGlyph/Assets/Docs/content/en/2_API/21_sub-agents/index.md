# Sub-Agents

`SubAgentScope` lets an agent dispatch background children. Each child is a full workflow agent over the same tree, holding a slice of its parent's capabilities. Dispatch is **spawn-and-poll**: a spawn returns a handle at once and the child runs behind it, because a spawn executes inside a tool call on the host's thread.

A child's allowance is a share of its parent's ledger, not a second pot. That is what makes an unbounded depth terminate, and why the root cap is the whole tree's cap.

## Namespaces

| Namespace | Types |
|---|---|
| `VeloxDev.AI.SubAgents` | `SubAgentScope`, `SubAgentAgentToolkit`, `SubAgentAgentContextProvider`, `SubAgentState`, `SubAgentSummary`, `SubAgentStatusViewModel`, `SubAgentTreeViewModel`, `SubAgentTreeNodeViewModel` |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope.WithSubAgents`, `WorkflowAgentScope.SubAgents` |

## Pages

- [SubAgentScope](00_sub-agent-scope/index.md) — creation, depth, budget, roster and disposal.
- [Dispatch tools](01_dispatch-tools/index.md) — the five model-facing tools and the fields a spawn accepts.
- [Roster](02_roster/index.md) — status rows, immutable summaries and the bindable tree.
- [Context provider](03_context-provider/index.md) — how the subsystem contributes itself to a turn.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tools a child inherits.
- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — the ledger the whole tree draws on.
