# Workflow Agent — Namespace: `VeloxDev.AI.MCP`

Local/remote MCP hosting: `McpScope` installs server packages (npm/pip), launches processes over stdio, or reaches remote servers over Streamable HTTP (SSE fallback), returning each server's tools as `AITool`; `McpAgentToolkit` turns server management into Agent-callable tools. All types below live in `VeloxDev.AI.MCP` (implemented in `Src/Core/VeloxDev.Core.Extension/Agent/MCP/`). Security model: server configuration is fixed once at load time; the Agent can only load/unload/inspect, never reconfigure.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/MCP/*`) + **Demo** (`AgentHelper` `Mcp`/`McpServers` + `McpAgentToolkit` registration).

## McpScope

`public class McpScope`. Manages the MCP installation root and the connect lifecycle. `McpScope.McpRootRelative` defaults to `".evn/mcp"` (relative to `AppContext.BaseDirectory`); runtimes live in `{root}/node/` (npm/npx), `{root}/py/` (pip/uvx), `{root}/dotnet/`, `{root}/exe/`.

| Member | Signature | Notes |
|---|---|---|
| `ServerError` | `event Action<McpServerConfiguration, Exception>?` | Raised when a server fails to load; the error is **not** rethrown and that server contributes zero tools. |
| `McpRootRelative` | `string { get; private set; }` | Current MCP root (relative). |
| `Status` | `McpStatusViewModel { get; }` | Globally bindable per-server status + aggregates, driven live during `LoadAsync`. |
| `LoadedTools` | `IReadOnlyList<AITool> { get; }` | All connected servers' tools, aggregated; changes mid-session (unload → tools disappear). |
| `WithMcpRoot` | `McpScope WithMcpRoot(string relativePath)` | Sets the install root. |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan?)` | Global connection/initialization timeout (Http mode); per-server override via `Options.connectionTimeout`. |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext?)` | Marshals all status updates onto the given UI context. |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string?>>)` | OAuth authorization-redirect handler for remote servers (opens `authorizationUri`, returns the final redirect URL carrying the code). When unset, the MCP SDK's default console-input handler is used. |
| `LoadAsync` | `Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)` | Loads servers in order. |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | Tools of one connected server (empty when not connected). |
| `UnloadServer` | `bool UnloadServer(string name)` | Removes a server's tool set and resets its status to `NotStarted`. Returns whether tools were loaded. |

**`LoadAsync` behavior.** `Npm`/`Pip` install first (idempotent, process-wide install cache + `SemaphoreSlim`), then connect over stdio; `Npx`/`Uvx`/`Dotnet`/`Exe` connect directly; `Http` connects over Streamable HTTP with SSE fallback. Per-server failure is caught — status becomes `McpServerStatus.Error`, `ServerError` fires, that server contributes zero tools; caller cancellation propagates. A remote connection respects `WithConnectionTimeout` with a host-side hard fallback.

## McpServerConfiguration

`public partial class McpServerConfiguration` — MVVM source-generated (`[VeloxProperty]`) properties.

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | Server name (status/tool key). |
| `Description` | `string` | Human-readable description. |
| `RunMode` | `McpServerRunMode` | How the server is launched / reached. |
| `Package` | `string` | Npm/Npx/Uvx/Pip package name; Dotnet: DLL path under `dotnet/` (e.g. `"sharp-email-mcp/SharpEmailMcp.dll"`); Exe: executable path under `exe/`. |
| `Version` | `string?` | Version tag for `Npm`/`Pip`; `null` = `"latest"`. |
| `Arguments` | `string[]` | Extra args passed to the server process. |
| `Endpoint` | `string?` | Remote URL for `Http` mode. |
| `Options` | `object?` | Anonymous-object blob (see below); unknown keys are rejected by `McpScope`. |

**`Options` keys.** Http: `headers` (extra headers), `oauth` (`clientId`, `clientSecret`, `redirectUri`, `scopes` — Authorization Code + PKCE), `connectionTimeout` (seconds or TimeSpan string; overrides the scope-wide value), `transportMode` (`AutoDetect`/`StreamableHttp`/`Sse`), `ownsSession`. Stdio: `env`, `workingDirectory`.

## McpServerRunMode

`enum McpServerRunMode` — how the server is reached:

| Mode | Command model |
|---|---|
| `Npm` | `npm install` into `{root}/node/{package}/`, then `node {entry} {args}`. |
| `Npx` | `npx -y {package} {args}` (temporary download, no install). |
| `Uvx` | `uvx {package} {args}` (uv provides its own isolation). |
| `Dotnet` | `dotnet {dll} {args}`; the user pre-publishes under `{root}/dotnet/{package}`. |
| `Pip` | Creates a venv at `{root}/py/venvs/{package}/`, `pip install`, then `python -m {module} {args}`. |
| `Exe` | Executes `{root}/exe/{package}` directly (tech-agnostic). |
| `Http` | Connects to a remote server at `Endpoint` (Streamable HTTP, SSE fallback); no local process. |

## McpServerStatus

`enum McpServerStatus` — connection lifecycle: `NotStarted`, `Installing` (local npm/pip only; Http skips it), `Connecting`, `Connected`, `Error`.

## Status view-models

`McpServerStatusViewModel` (per server): `Name`, `Description`, `RunMode`, `State`, `ToolCount`, `Error`, `Endpoint` plus derived `IsConnected`/`IsInstalling`/`IsConnecting`/`IsError` and Chinese `StateText` (`已连接`/`安装中`/`连接中`/`错误`/`未启动`).

`McpStatusViewModel` (aggregate, exposed by `McpScope.Status`): `Servers`, `IsLoading`, `ConnectedCount`, `ErrorCount`, `WorkingCount`, `IsAllReady`, `HasError`; methods `Track(McpServerStatusViewModel)`, `SetLoading(bool)`, `Reset()`.

## McpAgentToolkit

`public sealed class McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)` — MCP management tools callable by the Agent; register via `WorkflowAgentScope.WithTools(...)` (demo `AgentHelper.ProvideAgent`). Constructor throws `ArgumentNullException` when `scope` is null.

| Member | Signature | Notes |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools()` | Four tools: `ListMcpServers`, `LoadMcpServers`, `UnloadMcpServer`, `DescribeMcpServer`. |

| Tool | Purpose |
|---|---|
| `ListMcpServers` | Lists configured servers and status (`runMode`, `state`, `stateText`, `toolCount`, `error`) + aggregate counts. Pure query. |
| `LoadMcpServers` | Loads (installs if needed, connects) host pre-registered servers; optional JSON array of server names to load a subset. |
| `UnloadMcpServer` | Unloads a connected server mid-session (tools disappear from the next conversation; status resets to `NotStarted`). |
| `DescribeMcpServer` | Exports a connected server's tool capabilities (name + description) as prompts WITHOUT invoking them. |
