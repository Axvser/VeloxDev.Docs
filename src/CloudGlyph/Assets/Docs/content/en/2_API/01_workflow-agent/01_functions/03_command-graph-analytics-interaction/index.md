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

## Interaction (up to 4)

Registered purely by handler presence — there is no safety level any more. Both interaction tools are `AgentActionCategory.Interact`, which no permission mode ever puts to the user; the plan-mode pair is registered beside them and asks through the same confirmation handler.

| Tool | Registered when | Signature | Purpose |
|---|---|---|---|
| `RequestSelection` | `WithSelectionHandler` was called | `RequestSelection(string prompt, string optionsJson, string freeTextPrompt, bool allowMultiSelect = false)` | Presents single-/multi-choice + a free-text field and waits for the user. Returns `chosen` (single) / `chosenList` (multi) + `freeText`. |
| `RequestConfirmation` | `WithConfirmationHandler` was called | `RequestConfirmation(string operationKey, string description)` | Requests explicit confirmation: allow-once / allow-always-for-session / deny. Do not proceed if denied. |
| `EnterPlanMode` | `WithConfirmationHandler` was called | `EnterPlanMode()` | Asks the user, then moves the session to `AgentPermissionMode.Plan`, remembering the mode to restore. |
| `ExitPlanMode` | `WithConfirmationHandler` was called | `ExitPlanMode()` | Asks the user, then restores the mode the session was in before `Plan`. |

`RequestSelection` is backed by `WorkflowAgentScope.WithSelectionHandler`; `RequestConfirmation` by `WithConfirmationHandler`. The confirmation handler's key is the tool name for an `Ask` permission decision, and the model-supplied `operationKey` for this tool. `ResetToolCallLimit` also asks under `extend-tool-call-budget`.

## Example

```text
// Source: Test — ComposedProvidersTests / BudgetResetTests
SearchForward(nodeIndex: 0)                          → {"nodes":[{"i":1,"id":"...","t":"..."}]}
GetNodeStatistics(nodeIndex: 0)                      → {"inDegree":1,"outDegree":1,"totalConnections":2,...}
ExecuteCommandOnNode(0, "ReceiveCommand", null)      → {"status":"ok"}   // when allowlisted
RequestConfirmation("delete-all-nodes", "Delete every node") → {"status":"denied"|...}
```

**Expected result:** with no generic commands allowlisted, `ExecuteCommandOnNode` returns an error; with both handlers configured, `RequestSelection` / `RequestConfirmation` / `EnterPlanMode` / `ExitPlanMode` each appear exactly once in `ProvideTools()`.
