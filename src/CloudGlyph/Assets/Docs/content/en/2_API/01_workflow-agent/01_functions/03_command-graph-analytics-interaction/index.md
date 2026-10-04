# Functions · Command, Graph, Analytics & Interaction Tools

## Command — generic allowlisted execution (2)

Gated by `WithAllowedGenericCommands(...)`. Never called ⇒ generic command execution is disabled entirely (secure default); an unlisted command returns an error asking the host to allowlist it.

| Tool | Signature | Purpose |
|---|---|---|
| `ExecuteCommandOnNode` | `ExecuteCommandOnNode(int nodeIndex, string commandName, string? jsonParameter = null)` | Executes an allowlisted command on a node by index. Discover commands with `ListComponentCommands`. |
| `ExecuteCommandById` | `ExecuteCommandById(string runtimeId, string commandName, string? jsonParameter = null)` | Same, for any component (node/slot/link) by runtime ID. |

Backed by `CommandInvoker.Invoke`; the JSON parameter is deserialized to the type declared by `[AgentCommandParameter]`.

## Graph — traversal & path finding (5)

| Tool | Signature | Purpose |
|---|---|---|
| `SearchForward` | `SearchForward(int nodeIndex, string? typeName = null, int maxDepth = 0)` | BFS downstream; optional type-name substring filter; `0` = unlimited depth. |
| `SearchReverse` | `SearchReverse(int nodeIndex, string? typeName = null, int maxDepth = 0)` | BFS upstream. |
| `SearchAllRelative` | `SearchAllRelative(int nodeIndex, string? typeName = null, int maxDepth = 0)` | BFS both directions. |
| `IsConnected` | `IsConnected(int sourceNodeIndex, int targetNodeIndex, string direction = "forward")` | Direct/transitive connection check; `direction` = `"forward"` / `"reverse"` / `"any"`. |
| `FindPath` | `FindPath(int sourceNodeIndex, int targetNodeIndex)` | Shortest forward path (BFS); ordered `{i,id,t}` list or empty. |

All five are read-only queries (they never mark the tree dirty).

## Analytics (1)

| Tool | Signature | Purpose |
|---|---|---|
| `GetNodeStatistics` | `GetNodeStatistics(int nodeIndex)` | In-degree, out-degree, total connections, connected node ids, slot utilization. |

## Interaction (up to 2)

Registered **only** when the safety level is > 0 **and** the corresponding handler is configured. Both are read-only queries.

| Tool | Signature | Purpose |
|---|---|---|
| `RequestSelection` | `RequestSelection(string prompt, string optionsJson, string freeTextPrompt, bool allowMultiSelect = false)` | Presents single-/multi-choice + a free-text field and waits for the user. Returns `chosen` (single) / `chosenList` (multi) + `freeText`. |
| `RequestConfirmation` | `RequestConfirmation(string operationKey, string description)` | Requests explicit confirmation: allow-once / allow-always-for-session / deny. Do not proceed if denied. |

`RequestSelection` is backed by `WorkflowAgentScope.WithSelectionHandler`; `RequestConfirmation` by `WithConfirmationHandler`. The confirmation handler's key is the tool name for tool-approval, and the model-supplied `operationKey` for this tool.

## Example

```text
// Source: Test — ComposedProvidersTests / BudgetResetTests
SearchForward(nodeIndex: 0)                          → {"nodes":[{"i":1,"id":"...","t":"..."}]}
GetNodeStatistics(nodeIndex: 0)                      → {"inDegree":1,"outDegree":1,"totalConnections":2,...}
ExecuteCommandOnNode(0, "ReceiveCommand", null)      → {"status":"ok"}   // when allowlisted
RequestConfirmation("delete-all-nodes", "Delete every node") → {"status":"denied"|...}
```

**Expected result:** with no generic commands allowlisted, `ExecuteCommandOnNode` returns an error; with a level > 0 and a confirmation handler, `RequestConfirmation` appears exactly once in `ProvideTools()`.
