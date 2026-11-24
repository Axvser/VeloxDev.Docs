# Roster

The roster has two halves, each with a bindable and a thread-safe form. `SubAgentSummary` is the immutable copy an agent invocation reads; `SubAgentStatusViewModel` is the row a panel binds. The tree is a projection of several scopes' flat rosters.

## Pages

- [Summary and row](00_summary-and-row/index.md) — `SubAgentState`, `SubAgentSummary`, `SubAgentStatusViewModel`.
- [Tree](01_tree/index.md) — `SubAgentTreeViewModel` and `SubAgentTreeNodeViewModel`.

## Related

- [SubAgentScope](../00_sub-agent-scope/index.md) — the owner of the roster.
- [Dispatch tools](../01_dispatch-tools/index.md) — what creates the children.
