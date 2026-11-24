# McpScope

`VeloxDev.AI.MCP.McpScope : IAsyncDisposable` manages which MCP servers an agent may reach, their tools, and their status. Local servers are isolated under `.evn/mcp/{runtime}/` by run mode; remote servers connect over Streamable HTTP with an SSE fallback.

## Attachment to a workflow scope

| Member | Signature | Description |
|---|---|---|
| `WithMcps` | `WorkflowAgentScope WithMcps(McpScope mcp)` | Attaches the MCP scope. Loaded server tools join the per-turn tool set. |
| `Mcp` | `McpScope? Mcp { get; }` | The attached scope, or `null`. |

`WithMcps` also wires the MCP scope's confirmation handler to the workflow scope's own, so server self-service is gated by the same permission policy.

## Configuration members

| Member | Type / Signature | Description |
|---|---|---|
| `McpRootRelative` | `string` | Installation root, relative to the application base. Defaults to `.evn/mcp`. |
| `WithMcpRoot` | `McpScope WithMcpRoot(string relativePath)` | Sets that root. |
| `WithConfirmationHandler` | `McpScope WithConfirmationHandler(Func<string, string, Task<bool>> handler)` | Asks the user to approve an operation; returns `true` to proceed. With no handler, the answer is `false`. |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan? timeout)` | Global connection timeout for `Http` servers, with a host-side cancellation fallback. Per-server override via the `connectionTimeout` option. |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext? context)` | Marshals status updates to a UI thread. |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string?>> handler)` | Handles the OAuth redirect for remote servers. Defaults to the SDK's console-input handler. The returned URL must carry `state`, and `iss` when the authorization server sends one. |
| `WithServers` | `McpScope WithServers(params McpServerConfiguration[] servers)` | Pre-registers configurations the agent may later load **by name**. A later call with the same name replaces the earlier one. |
| `WithServersFromFile` | `McpScope WithServersFromFile(string path)` | Pre-registers servers from an `.mcp.json` document. |
| `RegisteredServers` | `IReadOnlyList<McpServerConfiguration>` | The configurations the agent may load by name. |

## Loading members

| Member | Signature | Description |
|---|---|---|
| `LoadAsync` | `Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)` | Loads the servers, **replacing** everything loaded before, and releases the replaced clients. Returns their tools. |
| `AddAsync` | `Task<AITool[]> AddAsync(McpServerConfiguration config, CancellationToken ct = default)` | Loads one server without disturbing the others. Returns its tools; empty on failure. |
| `LoadConfigurationFileAsync` | `Task<AITool[]> LoadConfigurationFileAsync(string path, CancellationToken ct = default)` | Loads an `.mcp.json` document with replace semantics. |
| `UnloadServer` | `bool UnloadServer(string name)` | Synchronous mid-session unload; returns whether any loaded tools were present. Blocks until disposal completes. |
| `UnloadServerAsync` | `Task<bool> UnloadServerAsync(string name)` | Async unload; the server can be loaded again later. |
| `LoadedTools` | `IReadOnlyList<AITool>` | All tools of currently connected servers, aggregated per server. |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | One connected server's tools; empty when not connected. |
| `DisposeAsync` | `ValueTask DisposeAsync()` | Disposes every connected client; for stdio modes this terminates child processes. Safe to call more than once. |

`LoadAsync` is destructive by design: it releases replaced clients so old stdio children do not outlive a reload. `AddAsync` is the incremental counterpart.

## Switches and version

| Member | Signature | Description |
|---|---|---|
| `SetServerEnabled` | `bool SetServerEnabled(string name, bool enabled)` | Drops or restores a server's tools without touching its connection. Works before the server is connected too. |
| `IsServerEnabled` | `bool IsServerEnabled(string name)` | Whether the server's tools are currently offered. |
| `DisabledServerNames` | `IReadOnlyList<string>` | Snapshot of the switched-off server names. |
| `SetToolEnabled` | `bool SetToolEnabled(string serverName, string toolName, bool enabled)` | Switches one tool of one server, independently of the server. Remembered across reloads. |
| `IsToolEnabled` | `bool IsToolEnabled(string serverName, string toolName)` | A tool is offered only when both it and its server are switched on. |
| `Version` | `long` | Monotonic version of the loaded-server set and switches; advances on load, add, unload and every switch. |

Disabling and unloading are different operations: disabling is instant, reversible and costs no reconnect; unloading tears the process or transport down.

## Status and prompts

| Member | Type / Signature | Description |
|---|---|---|
| `Status` | `McpStatusViewModel` | Bindable server status, driven live during loads. |
| `ServerError` | `event Action<McpServerConfiguration, Exception>?` | Raised when a server fails to load. The error is not rethrown. |
| `BuildInventoryBlock` | `string BuildInventoryBlock()` | A Markdown table of connected servers; empty when none are registered. Reads the status snapshot, not the bound collection. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | Creates the provider that contributes inventory, management tools and connected tools per turn. |

## Resource and prompt reading

| Member | Signature | Description |
|---|---|---|
| `ListResourcesAsync` | `Task<IReadOnlyList<McpClientResource>> ListResourcesAsync(string serverName, CancellationToken ct = default)` | Lists a connected server's resources. Throws when unknown or not connected. |
| `ReadResourceAsync` | `Task<ReadResourceResult> ReadResourceAsync(string serverName, string uri, CancellationToken ct = default)` | Reads one resource by URI or URI template. |
| `ListPromptsAsync` | `Task<IReadOnlyList<McpClientPrompt>> ListPromptsAsync(string serverName, CancellationToken ct = default)` | Lists a server's prompt templates. |
| `GetPromptAsync` | `Task<GetPromptResult> GetPromptAsync(string serverName, string promptName, IReadOnlyDictionary<string, object?>? arguments = null, CancellationToken ct = default)` | Expands one prompt with optional arguments. |

`McpClientResource`, `ReadResourceResult`, `McpClientPrompt` and `GetPromptResult` come from the `ModelContextProtocol` package, not from VeloxDev.

## Example

```csharp
using VeloxDev.AI.MCP;

var mcp = new McpScope();
mcp.WithServers(new McpServerConfiguration
{
    Name = "Microsoft Learn",
    RunMode = McpServerRunMode.Http,
    Endpoint = "https://learn.microsoft.com/api/mcp",
});

var tools = await mcp.LoadAsync(mcp.RegisteredServers);
```

## Related

- [Server configuration](../01_mcp-configuration/index.md) — what `WithServers` accepts.
- [Server status](../02_mcp-status/index.md) — the `Status` view-model.
