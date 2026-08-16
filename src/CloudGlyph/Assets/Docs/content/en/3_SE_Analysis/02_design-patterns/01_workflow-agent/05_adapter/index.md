# Workflow Agent — Design Patterns — Adapter

`LoadOneAsync` (a) installs the runtime for `Npm`/`Pip` (`EnsureNpmPackageAsync` / `EnsurePipPackageAsync`), (b) builds a transport — `StdioClientTransport` for local modes, `HttpClientTransport` for `Http` — and (c) creates an MCP client, lists its tools and casts them to `AITool`. Per-server failures become a `ServerError` event instead of a throw.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, lines 189-226 and 378-413

```csharp
private async Task<AITool[]> LoadOneAsync(McpServerConfiguration config, string mcpRoot, CancellationToken ct)
{
    var status = TrackServer(config);
    try
    {
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
        UpdateStatus(() => { status.ToolCount = tools.Length; status.State = McpServerStatus.Connected; });
        lock (_loadedToolsLock)
            _loadedToolSets[config.Name] = tools;
        return tools;
    }
    catch (Exception ex) when (ex is not OperationCanceledException)
    {
        UpdateStatus(() => { status.Error = ex.Message; status.State = McpServerStatus.Error; });
        ServerError?.Invoke(config, ex);
        return [];
    }
}
```
