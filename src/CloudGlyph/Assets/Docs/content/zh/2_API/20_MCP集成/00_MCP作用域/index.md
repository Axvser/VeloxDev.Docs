# McpScope

`VeloxDev.AI.MCP.McpScope : IAsyncDisposable` 管理智能体可触及的 MCP 服务器、它们的工具与状态。本地服务器按运行模式隔离在 `.evn/mcp/{runtime}/` 下；远程服务器经 Streamable HTTP 连接，并自动回退到 SSE。

## 挂载到工作流作用域

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithMcps` | `WorkflowAgentScope WithMcps(McpScope mcp)` | 挂载 MCP 作用域。已装载的服务器工具加入每轮工具集。 |
| `Mcp` | `McpScope? Mcp { get; }` | 已挂载的作用域，或 `null`。 |

`WithMcps` 还会把 MCP 作用域的确认处理器接到工作流作用域自己的处理器上，因此服务器自助受同一权限策略约束。

## 配置成员

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `McpRootRelative` | `string` | 安装根，相对应用基目录。默认 `.evn/mcp`。 |
| `WithMcpRoot` | `McpScope WithMcpRoot(string relativePath)` | 设置该根。 |
| `WithConfirmationHandler` | `McpScope WithConfirmationHandler(Func<string, string, Task<bool>> handler)` | 请用户批准操作；返回 `true` 继续。无处理器时答案为 `false`。 |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan? timeout)` | `Http` 服务器的全局连接超时，带宿主侧取消兜底。逐服务器可用 `connectionTimeout` 选项覆盖。 |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext? context)` | 把状态更新编组到 UI 线程。 |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string?>> handler)` | 处理远程服务器的 OAuth 重定向。默认使用 SDK 的控制台输入处理器。返回的 URL 必须携带 `state`，授权服务器发送了 `iss` 时也必须携带。 |
| `WithServers` | `McpScope WithServers(params McpServerConfiguration[] servers)` | 预注册智能体之后可**按名**装载的配置。同名后一次调用替换前一次。 |
| `WithServersFromFile` | `McpScope WithServersFromFile(string path)` | 从 `.mcp.json` 文档预注册服务器。 |
| `RegisteredServers` | `IReadOnlyList<McpServerConfiguration>` | 智能体可按名装载的配置。 |

## 装载成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `LoadAsync` | `Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)` | 装载服务器，**替换**此前装载的一切，并释放被替换的客户端。返回其工具。 |
| `AddAsync` | `Task<AITool[]> AddAsync(McpServerConfiguration config, CancellationToken ct = default)` | 装载一个服务器而不打扰其他服务器。返回其工具；失败时为空。 |
| `LoadConfigurationFileAsync` | `Task<AITool[]> LoadConfigurationFileAsync(string path, CancellationToken ct = default)` | 以替换语义装载 `.mcp.json` 文档。 |
| `UnloadServer` | `bool UnloadServer(string name)` | 同步会话中卸载；返回此前是否存在已装载工具。阻塞至释放完成。 |
| `UnloadServerAsync` | `Task<bool> UnloadServerAsync(string name)` | 异步卸载；之后可再次装载。 |
| `LoadedTools` | `IReadOnlyList<AITool>` | 所有已连接服务器的工具，按服务器聚合。 |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | 一个已连接服务器的工具；未连接时为空。 |
| `DisposeAsync` | `ValueTask DisposeAsync()` | 释放所有已连接客户端；stdio 模式会终止子进程。可多次调用。 |

`LoadAsync` 按设计具有破坏性：它释放被替换的客户端，使旧的 stdio 子进程不会比重载活得更久。`AddAsync` 是增量对应物。

## 开关与版本

| 成员 | 签名 | 说明 |
|---|---|---|
| `SetServerEnabled` | `bool SetServerEnabled(string name, bool enabled)` | 丢弃或恢复服务器工具而不碰其连接。服务器未连接前也可用。 |
| `IsServerEnabled` | `bool IsServerEnabled(string name)` | 服务器工具当前是否提供。 |
| `DisabledServerNames` | `IReadOnlyList<string>` | 被关闭服务器名称的快照。 |
| `SetToolEnabled` | `bool SetToolEnabled(string serverName, string toolName, bool enabled)` | 独立于服务器开关其中一个工具。按名记忆，跨重载保留。 |
| `IsToolEnabled` | `bool IsToolEnabled(string serverName, string toolName)` | 只有工具与其服务器都打开时才提供。 |
| `Version` | `long` | 已装载服务器集合与开关的单调版本号；装载、添加、卸载及每次开关都推进。 |

禁用与卸载是不同操作：禁用即时、可逆且无需重连；卸载会拆掉进程或传输，下次要重新付出代价。

## 状态与提示

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Status` | `McpStatusViewModel` | 可绑定服务器状态，装载期间实时驱动。 |
| `ServerError` | `event Action<McpServerConfiguration, Exception>?` | 服务器装载失败时触发。错误不会被重抛。 |
| `BuildInventoryBlock` | `string BuildInventoryBlock()` | 已连接服务器的 Markdown 表；未注册时为空。读取状态快照而非绑定集合。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 创建每轮贡献清单、管理工具与已连接工具的 provider。 |

## 资源与提示读取

| 成员 | 签名 | 说明 |
|---|---|---|
| `ListResourcesAsync` | `Task<IReadOnlyList<McpClientResource>> ListResourcesAsync(string serverName, CancellationToken ct = default)` | 列出已连接服务器的资源。未知或未连接时抛异常。 |
| `ReadResourceAsync` | `Task<ReadResourceResult> ReadResourceAsync(string serverName, string uri, CancellationToken ct = default)` | 按 URI 或 URI 模板读取一个资源。 |
| `ListPromptsAsync` | `Task<IReadOnlyList<McpClientPrompt>> ListPromptsAsync(string serverName, CancellationToken ct = default)` | 列出服务器的提示模板。 |
| `GetPromptAsync` | `Task<GetPromptResult> GetPromptAsync(string serverName, string promptName, IReadOnlyDictionary<string, object?>? arguments = null, CancellationToken ct = default)` | 展开一个提示，可带参数。 |

`McpClientResource`、`ReadResourceResult`、`McpClientPrompt` 与 `GetPromptResult` 来自 `ModelContextProtocol` 包，不是 VeloxDev。

## 示例

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

## 相关

- [服务器配置](../01_服务器配置/index.md) —— `WithServers` 接受什么。
- [服务器状态](../02_服务器状态/index.md) —— `Status` 视图模型。
