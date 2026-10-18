# 工作流代理 —— 设计模式 —— 适配器

`McpScope` 把外部 MCP 运行时适配成与 workflow 工具相同的 `AITool` 表面。`McpServerConfiguration` 声明服务器*如何*被触达（7 种 `McpServerRunMode`：`Npm`、`Npx`、`Uvx`、`Dotnet`、`Pip`、`Exe`、`Http`）；`LoadAsync` 把每份配置变成一组工具。

`LoadOneAsync` (a) 为 `Npm`/`Pip` 安装/准备运行时，(b) 构建传输 —— 本地模式用 `StdioClientTransport`，`Http` 用 `HttpClientTransport` —— (c) 创建 MCP 客户端、列出其工具并返回 `AITool[]`。单服务器失败会变成 `ServerError` 事件与空工具集，而不会中止整批。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`（`LoadAsync` / `LoadOneAsync`）

```csharp
private async Task<AITool[]> LoadOneAsync(McpServerConfiguration config, string mcpRoot, CancellationToken ct)
{
    var status = TrackServer(config);
    try
    {
        // 本地模式：先安装/准备运行时（Installing），再连接（Connecting）。
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

适配器再被 `McpAgentToolkit` 包一层，暴露六个管理工具（`ListMcpServers`、`LoadMcpServers`、`UnloadMcpServer`、`DescribeMcpServer`、`AddMcpServer`、`SetMcpServerArguments`）。宿主预注册 `McpServerConfiguration`；agent 能否增删改由会话的权限模式与规则在调用时决定，而不是由一份配置阶梯决定。

示例在 `AgentHelper.DemoMcpServers` 中注册 Microsoft Learn（远程 HTTP）、一个一次性远程端点，以及一个 npx 本地文件系统服务器（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`）。
