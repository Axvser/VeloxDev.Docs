# Agent Safety and Budgets

A workflow agent can edit a graph, run node business code and install MCP servers. `VeloxDev.AI.Safety` decides, per call, whether it may. The decision is a **named mode** plus a list of **rules**, and it is enforced at the call site rather than merely described in the prompt — so switching the mode governs the very next tool call.

The same package owns the **budgets** every call draws on: total calls, read calls, write calls, tokens and result size.

## What you will build

- an `AgentPermissionPolicy` and a table of decisions for the five action categories;
- rules that are stricter than any mode, including a `Deny` that holds in `Bypass`;
- a scope configured with a mode, rules, a judge and call budgets.

## Pages

- [Setup](00_setup/index.md) — prerequisites, the package, and the first policy.
- [Usage](01_usage/index.md) — the mode matrix, rule patterns, the judge, budget semantics, and the complete program.

## The two layers

| Layer | What it is | Can it be stricter than a mode? |
|---|---|---|
| `AgentPermissionMode` | the coarse state the user names and switches | — |
| `AgentPermissionRule` | a pattern with `Allow` / `Ask` / `Deny` | yes, including in `Bypass` |

`AgentActionCategory` is a **call-time classification** (`Read`, `Edit`, `Execute`, `Curate`, `Interact`). It is deliberately not `WorkflowToolCategory`, which is only a surface filter deciding what is sent to the model.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tool surface these rules govern.
- [MCP Integration](../20_mcp-integration/index.md) — the `Curate` calls a mode treats most carefully.
