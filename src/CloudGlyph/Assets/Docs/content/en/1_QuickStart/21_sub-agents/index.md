# Sub-Agents

`SubAgentScope` lets an agent dispatch background children. Each child is a full workflow agent over the same tree, holding a slice of its parent's capabilities. Dispatch is **spawn-and-poll**: a spawn returns a handle at once and the child runs behind it, because a spawn executes inside a tool call on the host's UI thread and a synchronous child would hold that thread for its whole conversation.

A child's allowance is a share of its parent's ledger, not a second pot. That is what makes an unbounded depth terminate, and it is why the root cap is the whole tree's cap.

## What you will build

- a `SubAgentScope` from a chat client, with a depth limit and a spawn budget;
- the five dispatch tools the model calls;
- the roster an operator watches, both as bindable rows and as a thread-safe snapshot.

## Pages

- [Setup](00_setup/index.md) — prerequisites, the package, the factory, and attachment order.
- [Usage](01_usage/index.md) — the dispatch tools, narrowing, the budget contract, the roster, and the complete program.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tools a child inherits.
- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — the budget the whole tree draws on.
