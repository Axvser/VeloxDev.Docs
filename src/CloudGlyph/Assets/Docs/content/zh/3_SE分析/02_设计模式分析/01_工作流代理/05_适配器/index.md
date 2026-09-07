# Workflow Agent — 设计模式 — 适配器

`McpScope` 把外部 MCP 运行时适配进与工作流工具相同的 `AITool` 表面。`McpServerConfiguration` 声明服务器*如何*被触达（7 种 `McpServerRunMode`：`Npm`、`Npx`、`Uvx`、`Dotnet`、`Pip`、`Exe`、`Http`）；`LoadAsync` 把每个配置转成一组工具。

`LoadOneAsync`（a）为 `Npm`/`Pip` 安装/准备运行时，（b）构建传输——本地模式用 `StdioClientTransport`、`Http` 用 `HttpClientTransport`，（c）创建 MCP 客户端、列出工具并以 `AITool[]` 返回。单服务器失败变成 `ServerError` 事件与空工具集，而非中止整批。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`，第 193-230 与 300-418 行

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

适配器再被 `McpAgentToolkit` 包裹，暴露四个管理工具（`ListMcpServers`、`LoadMcpServers`、`UnloadMcpServer`、`DescribeMcpServer`）。宿主预先注册 `McpServerConfiguration`；agent 只能加载/卸载/检查，绝不能重新配置——配置一旦加载即不可变（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpAgentToolkit.cs`）。

Demo 在 `AgentHelper.DemoMcpServers` 中注册了 Microsoft Learn（远程 HTTP）、一个一次性远程端点以及一个经 npx 启动的本地文件系统服务器（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 37-68 行）。
