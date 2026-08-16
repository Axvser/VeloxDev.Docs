# Workflow Agent — 设计模式 — 适配器

`LoadOneAsync`（a）为 `Npm`/`Pip` 安装运行时（`EnsureNpmPackageAsync` / `EnsurePipPackageAsync`），（b）构建传输 —— 本地模式用 `StdioClientTransport`、`Http` 用 `HttpClientTransport`，（c）创建 MCP 客户端、列出工具并转换为 `AITool`。单服务器失败变成 `ServerError` 事件而非抛出。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`，第 189-226 与 378-413 行

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
