# Data Flow — MCP Server Load

`McpAgentToolkit.LoadMcpServers` funnels into `McpScope.LoadAsync`. Each `McpServerConfiguration` becomes a tool set: local modes install/prepare the runtime (memoized process-wide), `ConnectServerAsync` builds a `StdioClientTransport` (or `HttpClientTransport` for `Http`) and performs the JSON-RPC `initialize`/`tools/list` handshake, and the returned tools are added to `McpScope.LoadedTools` so the per-conversation tool set (`base tools + LoadedTools`) reflects them on the next call.

```plantuml
@startuml
actor Host
participant "McpAgentToolkit.LoadMcpServers" as Mtool
participant "McpScope" as Mcp
participant "McpStatusViewModel" as Status
participant "CliWrap (npm / pip / uv)" as Shell
participant "StdioClientTransport / HttpClientTransport" as Trans
participant "MCP server process (node/dotnet/python/exe)" as Server
participant "McpClient (SDK)" as SDK

Host -> Mtool: LoadMcpServers(namesJson?)
activate Mtool
Mtool -> Mcp: LoadAsync(subset, ct)
activate Mcp
Mcp -> Status: Reset(); SetLoading(true); Track(config)

loop for each selected server
    Mcp -> Mcp: TrackServer(config) / LoadOneAsync(config)
    alt Npm or Pip mode
        Mcp -> Shell: EnsureNpmPackageAsync / EnsurePipPackageAsync (CliWrap)
        Shell -> Shell: memoized key "node:/py:package@version" guarded by SemaphoreSlim
        alt already installed
            Shell --> Mcp: skip (idempotent)
        else fresh install
            Shell -> Shell: npm install / python -m venv + pip install
            Shell --> Mcp: exit 0 (or throw)
        end
    end
    Mcp -> Trans: ConnectServerAsync: StdioClientTransport / CreateHttpTransport
    Trans -> Server: spawn/connect process (npx/uvx/dotnet/exe/node/pip -m)
    Server --> Trans: stdio pipe / HTTP endpoint
    Trans -> SDK: McpClient.CreateAsync(transport, options, ct)
    SDK -> Server: JSON-RPC initialize / tools/list
    Server --> SDK: tool schemas
    SDK --> Trans: ListToolsAsync()
    Trans --> Mcp: AITool[]
    Mcp -> Status: State = Connected; ToolCount = N
    Mcp -> Mcp: _loadedToolSets[name] = tools
    alt per-server failure (not cancellation)
        Mcp -> Status: State = Error; Error = message
        Mcp -> Host: ServerError(config, ex)  -- error NOT rethrown
        note right: contributes zero tools; batch continues
    end
end

Mcp --> Mtool: AITool[] aggregated
deactivate Mcp
Mtool --> Host: updated server status JSON
deactivate Mtool
@enduml
```

Notes:

- The `Http` run mode performs no install and connects to `Endpoint` (Streamable HTTP with SSE fallback); optional `headers`/`oauth`/`connectionTimeout`/`transportMode`/`ownsSession` come from `McpServerConfiguration.Options` (unknown keys are rejected).
- Cancellation propagates as `OperationCanceledException` (not caught by the per-server handler). Status updates marshal to the UI context when `WithSynchronizationContext` is registered.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, `LoadAsync` lines 167-191, `LoadOneAsync` lines 193-230, `EnsureNpmPackageAsync` lines 300-332, `ConnectServerAsync` lines 382-418; `McpAgentToolkit.cs` `LoadServers` lines 120-162.
