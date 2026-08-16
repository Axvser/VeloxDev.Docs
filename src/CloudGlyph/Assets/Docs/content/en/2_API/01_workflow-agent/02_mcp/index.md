# Workflow Agent — Namespace: `VeloxDev.AI.MCP`

### `McpScope`

Local MCP environment: installs server packages and connects over stdio (or remote HTTP), returning tools as `AITool[]`.

#### `WithMcpRoot`

**Signature:** `public McpScope WithMcpRoot(string relativePath)`
**Returns:** the same scope.
**Notes:** root is relative to `AppContext.BaseDirectory`; default `".evn/mcp"`. Runtime subdirectories: `{root}/node/` (npm/npx), `{root}/py/` (pip/uvx), `{root}/dotnet/`, `{root}/exe/`.

#### `LoadAsync`

**Signature:** `public async Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)`
**Returns:** all loaded server tools as `AITool[]`.
**Exceptions:** none thrown for per-server failures — the `ServerError` event is raised and that server contributes zero tools. `OperationCanceledException` propagates on cancellation.
**Example:** `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, lines 163–187; demo `AgentHelper.LoadMcpServersAsync`.
**Notes:** local modes (`Npm`/`Pip`) install first (idempotent, process-wide `s_installed` set + `SemaphoreSlim`), then connect via stdio; `Npx`/`Uvx`/`Dotnet`/`Exe` connect directly; `Http` connects over Streamable HTTP (SSE fallback). Status is driven on `Status` (`McpStatusViewModel`), marshalled to the UI thread when a synchronization context is registered.

#### `ServerError`

**Signature:** `public event Action<McpServerConfiguration, Exception>? ServerError`
**Notes:** raised when a server fails to load; the error is not rethrown. Per-server status becomes `McpServerStatus.Error`.

#### Other members

| Member | Signature | Effect |
|---|---|---|
| `McpRootRelative` | `string { get; }` | Current MCP root (relative). |
| `Status` | `McpStatusViewModel { get; }` | Global bindable per-server status + aggregates. |
| `LoadedTools` | `IReadOnlyList<AITool> { get; }` | All connected servers' tools, aggregated; changes mid-session. |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | Tools of one connected server (empty if not connected). |
| `UnloadServer` | `bool UnloadServer(string name)` | Removes a server's tools and resets its status to `NotStarted`. |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan?)` | Global connection timeout (Http mode). |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext?)` | Marshal status updates to the UI thread. |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string>>)` | OAuth authorization-redirect handler for remote servers. |

### `McpServerConfiguration`

**Signature:** `public partial class McpServerConfiguration` (MVVM source-generated properties)

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Server name (status/tool key). |
| `Description` | `string` | Human-readable description. |
| `RunMode` | `McpServerRunMode` | How the server is launched / reached. |
| `Package` | `string` | Npm/PyPI package name, DLL path under `dotnet/`, or exe path under `exe/`. Note: property name is **`Package`**, not `NpmPackage`. |
| `Version` | `string?` | Version tag (Npm/Pip); `null` = `"latest"`. |
| `Arguments` | `string[]` | Extra args passed to the server process. |
| `Endpoint` | `string?` | Remote URL for `Http` mode. |
| `Options` | `object?` | Anonymous-object blob; known keys `headers`, `oauth`, `connectionTimeout`, `transportMode`, `ownsSession`, `env`, `workingDirectory`; unknown keys are rejected. |

### `McpServerRunMode`

`Npm` (npm install + node), `Npx` (npx -y), `Uvx` (uvx), `Dotnet` (dotnet {dll}), `Pip` (venv + pip install + python -m), `Exe` (direct executable), `Http` (remote Streamable HTTP/SSE). The previous doc revision listed six modes; `Http` is the current seventh.

### `McpServerStatus`

`NotStarted`, `Installing`, `Connecting`, `Connected`, `Error`.

### `McpStatusViewModel` / `McpServerStatusViewModel`

Bindable per-server status (`Name`, `Description`, `RunMode`, `State`, `ToolCount`, `Error`, `Endpoint`, derived `IsConnected`/`IsInstalling`/`IsConnecting`/`IsError`/`StateText`) and the aggregate VM (`Servers`, `IsLoading`, `ConnectedCount`, `ErrorCount`, `WorkingCount`, `IsAllReady`, `HasError`; `Track`, `SetLoading`, `Reset`).

### `McpAgentToolkit`

Agent-callable MCP management tools, registered via `WorkflowAgentScope.WithTools(...)`.

**Signature:** `public sealed class McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)` — `CreateTools()` returns four tools:

| Tool | Purpose |
|---|---|
| `ListMcpServers` | Lists configured servers and status (state, tool count, error) + aggregate counts. |
| `LoadMcpServers` | Loads (installs if needed, connects) host pre-registered servers, optional name subset. |
| `UnloadMcpServer` | Unloads a connected server mid-session. |
| `DescribeMcpServer` | Exports a connected server's tool capabilities as prompts without invoking them. |

Security model: server configuration is fixed at load time; the Agent can only load/unload/inspect, never reconfigure.
