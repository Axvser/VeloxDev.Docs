# Workflow Agent — Design Patterns — Adapter

`McpScope` adapts external MCP runtimes into the same `AITool` surface the workflow tools use. `McpServerConfiguration` declares *how* a server is reached (7 `McpServerRunMode`s: `Npm`, `Npx`, `Uvx`, `Dotnet`, `Pip`, `Exe`, `Http`); `LoadAsync` turns each config into a set of tools.

`LoadOneAsync` (a) installs/prepares the runtime for `Npm`/`Pip`, (b) builds a transport — `StdioClientTransport` for local modes, `HttpClientTransport` for `Http` — and (c) creates the MCP client, lists its tools and returns them as `AITool[]`. A per-server failure becomes a `ServerError` event and an empty tool set instead of aborting the batch.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, lines 193-230 and 300-418

```csharp
private async Task<AITool[]> LoadOneAsync(McpServerConfiguration config, string mcpRoot, CancellationToken ct)
{
    var status = TrackServer(config);
    try
    {
        // Local mode: first install/prepare the runtime (Installing), then connect (Connecting).
        if (config.RunMode is McpServerRunMode.Npm or McpServerRunMode.Pip)
        {
            SetServerState(status, McpServerStatus.Installing);
            if (config.RunMode == McpServerRunMode.Npm)
                await EnsureNpmPackageAsync(config.Package, config.Version, mcpRoot, ct);
            else
                await EnsurePipPackageAsync(config.Package, config.Version, mcpRoot, ct);
        }

        SetServerState(status, McpServerStatus.Connecting);
        var tools = await ConnectServerAsync(config, mcpRoot, ct);

        UpdateStatus(() =>
        {
            status.ToolCount = tools.Length;
            status.State = McpServerStatus.Connected;
        });
        lock (_loadedToolsLock)
            _loadedToolSets[config.Name] = tools;
        return tools;
    }
    catch (Exception ex) when (ex is not OperationCanceledException)
    {
        UpdateStatus(() =>
        {
            status.Error = ex.Message;
            status.State = McpServerStatus.Error;
        });
        ServerError?.Invoke(config, ex);
        return [];
    }
}
```

The adapter is wrapped further by `McpAgentToolkit`, which exposes four management tools (`ListMcpServers`, `LoadMcpServers`, `UnloadMcpServer`, `DescribeMcpServer`). The host pre-registers the `McpServerConfiguration`s; the agent can only load/unload/inspect them, never reconfigure — configuration is immutable once loaded (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpAgentToolkit.cs`).

The demo registers Microsoft Learn (remote HTTP), a throwaway remote endpoint, and a local filesystem server via npx in `AgentHelper.DemoMcpServers` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 37-68).
