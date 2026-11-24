# Server status

MCP status follows the same two-view pattern as skills: a bindable row per server, and an immutable snapshot safe to read from the thread that renders the prompt.

## Enum: McpServerStatus

| Member | Meaning |
|---|---|
| `NotStarted` | Configured but not loaded. |
| `Installing` | Installing the runtime (local npm/pip). |
| `Connecting` | Launching the process or handshaking with a remote. |
| `Connected` | Alive; tools are available. |
| `Error` | Load failed. |

## Class: McpServerStatusViewModel

One server as a bindable row, generated from `[VeloxProperty]` fields.

### Generated properties

| Name | Type | Description |
|---|---|---|
| `Name` | `string` | Server name. |
| `Description` | `string` | Operator-facing description. |
| `RunMode` | `McpServerRunMode` | How the server is launched. |
| `State` | `McpServerStatus` | Raw lifecycle state. |
| `ToolCount` | `int` | Number of tools the server exposes. |
| `Error` | `string?` | Failure text when `State == Error`. |
| `Endpoint` | `string?` | Remote endpoint, when not launched locally. |
| `IsEnabled` | `bool` | Whether the server's tools reach the agent. Default `true`. |

### Computed members

| Name | Type | Description |
|---|---|---|
| `IsConnected` | `bool` | `State == Connected`. |
| `IsActive` | `bool` | `IsConnected && IsEnabled` — the only state in which tools are offered. |
| `IsInstalling` | `bool` | `State == Installing`. |
| `IsConnecting` | `bool` | `State == Connecting`. |
| `IsError` | `bool` | `State == Error`. |
| `StateText` | `string` | Display text for the state. |

Disabling a server keeps it `Connected` and keeps its tools loaded; it simply stops offering them. That is different from unloading, which tears the connection down.

## Class: McpServerSummary

An immutable copy of one server's state, safe from any thread. It carries everything a row needs, so a scope built from a snapshot can reconstruct its rows without tracked servers.

| Member | Type | Description |
|---|---|---|
| `Name` | `string` | Server name. |
| `Description` | `string` | Operator-facing description. |
| `RunMode` | `McpServerRunMode` | Launch mode. |
| `State` | `McpServerStatus` | Raw lifecycle state. |
| `StateText` | `string` | Display text. |
| `ToolCount` | `int` | Tools currently exposed. |
| `Error` | `string?` | Load failure text. |
| `Endpoint` | `string?` | Remote endpoint. |
| `IsEnabled` | `bool` | Whether tools reach the agent. |
| `IsActive` | `bool` | Connected and switched on. |

## Class: McpStatusViewModel

The globally bindable status view-model held by `McpScope.Status`.

| Member | Type / Signature | Description |
|---|---|---|
| `Servers` | `ObservableCollection<McpServerStatusViewModel>` | The bindable rows, generated from the tracked collection. |
| `Snapshot` | `IReadOnlyList<McpServerSummary>` | Immutable copy, republished on the bound thread when any tracked server changes. |
| `ConnectedCount` | `int` | Connected servers. |
| `ErrorCount` | `int` | Failed servers. |
| `WorkingCount` | `int` | Servers installing or connecting. |
| `IsAllReady` | `bool` | No server is installing, connecting or failed. |
| `HasError` | `bool` | At least one server failed. |
| `Track` | `void Track(McpServerStatusViewModel server)` | Registers a row and subscribes to its changes. Call on the UI thread. |
| `SetLoading` | `void SetLoading(bool loading)` | Sets the batch-loading flag and refreshes the aggregates. |
| `Reset` | `void Reset()` | Clears all server status; call before reloading. |

A prompt is rendered on the agent-invocation thread, so read `Snapshot` — not `Servers` — from anywhere that is not the bound thread.

## Example

```csharp
Console.WriteLine(mcp.Status.IsAllReady);
foreach (var server in mcp.Status.Snapshot)
    Console.WriteLine($"{server.Name} {server.StateText} {server.ToolCount}");
```

## Related

- [McpScope](../00_mcp-scope/index.md) — the owner of `Status`.
- [MCP tools](../03_mcp-tools/index.md) — the tools that report these states to the model.
