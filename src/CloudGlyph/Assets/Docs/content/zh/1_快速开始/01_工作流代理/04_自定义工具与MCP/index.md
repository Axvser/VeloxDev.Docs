# 工作流代理 — 自定义工具与 MCP

在内置工具包之上，你可以注册自己的工具，也可以用 Model Context Protocol 服务器扩展代理，让它们的工具合并进每一轮对话。

## 1. 注册自定义工具

`WithTools` 与 `WithQueryTools` 把额外的 `AITool` 追加到 `ProvideTools()` 返回的表面。两者都接受一个会变成系统提示词「Custom Tools」段的 `promptContext` 字符串，以及一组工具参数：

```csharp
AITool serverStatus = AIFunctionFactory.Create(
    () => $"workflow nodes: {scope.Tree.Nodes.Count}", "ServerStatus");

AITool readOnlyClock = AIFunctionFactory.Create(
    () => DateTimeOffset.Now.ToString("O"), "ReadOnlyClock");

scope.WithTools("ServerStatus 报告当前工作流节点数量。", serverStatus);
scope.WithQueryTools("ReadOnlyClock 返回当前时间；它从不修改树。", readOnlyClock);
```

`AITool` 与 `AIFunctionFactory` 来自 `Microsoft.Extensions.AI`；`scope` 是上一页构建的 `WorkflowAgentScope`。

- `WithTools` 注册可变更的工具：`AIFunction` 会拿到一个**跟踪包装**（UI 线程编组、预算计数、工具回调与自动置脏）。`WithQueryTools` 注册只读工具，行为一致，只是从不触发自动置脏、并按读预算计数。
- 非 `AIFunction` 工具（例如一个原始 MCP 客户端工具）会原样添加，不加跟踪包装。

**预期结果：** 注册后 `scope.ProvideTools()` 包含 `ServerStatus` 与 `ReadOnlyClock`；调用 `ReadOnlyClock` 从不把树置脏。

## 2. 用 `McpScope` 加载 MCP 服务器

`McpScope`（`VeloxDev.AI.MCP`）加载服务器并把它们的工具暴露为 `AITool`。每个服务器用一个 `McpServerConfiguration` 描述，其 `RunMode` 决定启动策略：

```csharp
var mcp = new McpScope()                          // 默认安装进 ".evn/mcp"
    .WithMcpRoot(".evn/mcp")                      // 如需可覆盖安装根目录
    .WithConnectionTimeout(TimeSpan.FromSeconds(30));

McpServerConfiguration[] servers =
[
    new()                                          // 远程 Streamable HTTP：无需本地运行时
    {
        Name = "Microsoft Learn",
        Description = "微软官方文档检索（远程 Streamable HTTP）",
        RunMode = McpServerRunMode.Http,
        Endpoint = "https://learn.microsoft.com/api/mcp",
        Options = new { connectionTimeout = 30 },
    },
    new()                                          // 本地 npx 服务器
    {
        Name = "Filesystem",
        RunMode = McpServerRunMode.Npx,
        Package = "@modelcontextprotocol/server-filesystem",
        Arguments = [AppContext.BaseDirectory],
        Options = new { env = new { FILESYSTEM_ROOT = AppContext.BaseDirectory } },
    },
];

AITool[] mcpTools = await mcp.LoadAsync(servers);
```

- `McpServerConfiguration` 字段：`Name`、`Description`、`RunMode`、`Package`、`Version`、`Arguments`（字符串数组）、`Endpoint`，以及任意的 `Options` 对象。`McpServerRunMode` 成员：`Npm`、`Npx`、`Uvx`、`Dotnet`、`Pip`、`Exe`、`Http`。
- `Http` 用 `Endpoint` + `Options`（headers、OAuth、`connectionTimeout`、`transportMode`、`ownsSession`）走 Streamable HTTP 连接。stdio 模式（`Npx` 等）会把 `Package` 安装进 `McpRootRelative` 并按 `Package`/`Version`/`Arguments`/`Options.env`/`Options.workingDirectory` 通过 stdio 连接。
- `McpScope` 还提供 `WithSynchronizationContext`（把加载/状态回调编组到 UI 线程）与 `WithOAuthAuthorizationRedirect((authUri, redirectUri, ct) => ...)`（用于 HTTP OAuth）。加载后：`mcp.LoadedTools` 是已连接服务器的工具，`mcp.GetServerTools(name)` 是单服务器工具，`mcp.UnloadServer(name)` 会话中途移除一个，`mcp.Status` 是实时的 `McpStatusViewModel`（逐服务器状态、连接/错误计数）。

**预期结果：** `LoadAsync` 返回已连接服务器的工具为 `AITool[]`；每个工具名前缀带服务器名；连接失败的服务器不会抛出，而是以 `Error` 状态记入 `mcp.Status`。

## 3. 经 `McpAgentToolkit` 把服务器交给代理

存在两个不同的设计点：你可以自己把*服务器*工具合并进对话（见下一页），也可以让*代理*用 `McpAgentToolkit` 管理宿主预注册的服务器：

```csharp
var mcp = new McpScope();                          // 一个共享加载器
McpServerConfiguration[] hostConfigs = [...];      // 宿主在加载时一次固定，之后不可改

scope.WithTools(
    "MCP 服务器管理工具：ListMcpServers 报告每个服务器的状态；" +
    "DescribeMcpServer 导出一个已连接服务器的工具能力提示词；" +
    "LoadMcpServers 加载宿主预注册的服务器（需要时安装并连接）；" +
    "UnloadMcpServer 在会话中途移除一个服务器。配置由宿主固定，之后无法修改。",
    [.. new McpAgentToolkit(mcp, hostConfigs).CreateTools()]);
```

`McpAgentToolkit.CreateTools()` 返回四个面向代理的工具 —— `ListMcpServers`、`DescribeMcpServer`、`LoadMcpServers`、`UnloadMcpServer`。因为是通过 `WithTools` 注册的，代理可以会话中途检查并加载服务器，但**不能重新配置它们**：服务器配置在加载时一次固定。加载本地服务器会安装 npm/pip 运行时且可能较慢，所以提示词指示代理先与用户确认。

**预期结果：** `ProvideTools()` 包含四个 `Mcp*` 管理工具；代理调用 `LoadMcpServers` 后，对应服务器的工具出现在 `mcp.LoadedTools` 与下一轮对话的工具集里。

## 运行声明

- ⚠️ 仅静态核验。API 名称、`McpServerConfiguration` 字段、`McpServerRunMode` 成员与行为取自 `Src/Core/VeloxDev.Core.Extension/Agent/MCP/*` 与演示 `AgentHelper.cs`；本次文档编写未真正加载任何服务器。
