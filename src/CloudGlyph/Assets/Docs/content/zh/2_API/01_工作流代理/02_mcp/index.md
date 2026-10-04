# 工作流代理 —— 命名空间：`VeloxDev.AI.MCP`

本地/远程 MCP 托管：`McpScope` 安装服务器包（npm/pip）、经 stdio 启动进程，或经 Streamable HTTP（SSE 回退）触达远程服务器，并把每个服务器的工具作为 `AITool` 返回；`McpAgentToolkit` 把服务器管理变成 Agent 可调用的工具，`McpAgentContextProvider` 每轮贡献它们（以及清单）。所有类型位于 `VeloxDev.AI.MCP`（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/MCP/`）。安全模型：配置在加载时固定；Agent 可加载/卸载/查看，只有在宿主打开自助阶梯时才能新建服务器。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/MCP/*`）+ **Demo**（`AgentHelper` 的 `Mcp`/`McpServers`，`WithMcps`）。

## McpScope

`public class McpScope`。管理 MCP 安装根与连接生命周期。`McpRootRelative` 默认 `".evn/mcp"`；运行时位于 `{root}/node/`、`{root}/py/`、`{root}/dotnet/`、`{root}/exe/`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ServerError` | `event Action<McpServerConfiguration, Exception>?` | 服务器加载失败时触发；不重抛，该服务器贡献零个工具。 |
| `McpRootRelative` | `string { get; private set; }` | 当前 MCP 根（相对）。 |
| `SelfServiceLevel` | `McpSelfServiceLevel { get; private set; }` | 默认 `Closed`。 |
| `Status` | `McpStatusViewModel { get; }` | 可绑定的逐服务器状态 + 聚合。 |
| `Version` | `long { get; }` | 渲染缓存键；服务器/级别变化时前进。 |
| `LoadedTools` | `IReadOnlyList<AITool> { get; }` | 所有已连接服务器的工具，聚合。 |
| `DisabledServerNames` | `IReadOnlyList<string> { get; }` | 被宿主关闭的服务器。 |
| `RegisteredServers` | `IReadOnlyList<McpServerConfiguration> { get; }` | 经 `WithServers` 预注册的配置。 |
| `WithMcpRoot` | `McpScope WithMcpRoot(string relativePath)` | 设置安装根。 |
| `WithSelfService` | `McpScope WithSelfService(McpSelfServiceLevel level)` | 打开自助阶梯。 |
| `WithConfirmationHandler` | `McpScope WithConfirmationHandler(Func<string, string, Task<bool>> handler)` | 自助新增的用户审批回调。 |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan? timeout)` | 全局 HTTP 传输 + 初始化超时。 |
| `WithServers` | `McpScope WithServers(params McpServerConfiguration[] servers)` | 预注册可加载配置。 |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext? context)` | 编组状态更新。 |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string?>> handler)` | 远程服务器的 OAuth 授权重定向处理器。 |

**其他公开方法。** `CanAddServer(McpServerRunMode)`、`RequiresConfirmationToAdd()`、`SetServerEnabled(string, bool)`、`IsServerEnabled(string)`、`SetToolEnabled(string serverName, string toolName, bool)`、`IsToolEnabled(string serverName, string toolName)`、`BuildInventoryBlock()`、`CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)`、`UnloadServer(string)`、`UnloadServerAsync(string)`、`DisposeAsync()`、`LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)`、`AddAsync(McpServerConfiguration config, CancellationToken ct = default)`、`GetServerTools(string name)`。

**`LoadAsync` 行为。** `Npm`/`Pip` 先安装（幂等，进程级安装缓存 + `SemaphoreSlim`），再经 stdio 连接；`Npx`/`Uvx`/`Dotnet`/`Exe` 直接连接；`Http` 经 Streamable HTTP 连接，SSE 回退。逐服务器失败被捕获 —— 状态变为 `Error`，触发 `ServerError`，该服务器贡献零个工具；调用方取消会传播。

**服务器/工具开关。** `SetServerEnabled(name, false)` 丢弃服务器的工具但保持连接（无需重连即可还原）；`SetToolEnabled(server, tool, false)` 独立关闭某个工具（两个服务器上同名工具各自独立切换）。每次真实开关都推进 `Version`，使上下文提供器重新渲染；在服务器出现前所做的开关会被记住。

## McpServerConfiguration

`public partial class McpServerConfiguration` —— MVVM 源生成的（`[VeloxProperty]`）属性。

| 属性 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 服务器名（状态/工具键）。 |
| `Description` | `string` | 可读描述。 |
| `RunMode` | `McpServerRunMode` | 启动/触达方式。 |
| `Package` | `string` | 按模式的包名/路径。 |
| `Version` | `string?` | `Npm`/`Pip` 的版本标签；`null` = `"latest"`。 |
| `Arguments` | `string[]` | 传给服务器进程的额外参数。 |
| `Endpoint` | `string?` | `Http` 模式的远程 URL。 |
| `Options` | `object?` | 匿名对象 blob；未知键被拒绝。 |

**`Options` 键。** Http：`headers`、`oauth`（`clientId`、`clientSecret`、`redirectUri`、`scopes` —— Authorization Code + PKCE）、`connectionTimeout`、`transportMode`（`AutoDetect`/`StreamableHttp`/`Sse`）、`ownsSession`。Stdio：`env`、`workingDirectory`。

## 枚举

`enum McpServerRunMode` —— `Npm`、`Npx`、`Uvx`、`Dotnet`、`Pip`、`Exe`、`Http`（命令模型见快速开始页）。

`enum McpServerStatus` —— `NotStarted`、`Installing`、`Connecting`、`Connected`、`Error`。

`enum McpSelfServiceLevel` —— `Closed = 0`、`RemoteConfirmed = 1`、`AllConfirmed = 2`、`Unrestricted = 3`。`RemoteConfirmed` 只开放 `Http`；`AllConfirmed` 也开放本地模式但仍会询问；`Unrestricted` 不再询问。`CanAddServer(mode)` / `RequiresConfirmationToAdd()` 读它。

## 状态视图模型

`McpServerStatusViewModel`（每服务器）：`Name`、`Description`、`RunMode`、`State`、`ToolCount`、`Error`、`Endpoint`、`IsEnabled`，外加派生的 `IsConnected`/`IsActive`/`IsInstalling`/`IsConnecting`/`IsError` 与中文 `StateText`（`已连接`/`安装中`/`连接中`/`错误`/`未启动`）。

`McpServerSummary` —— 携带同样事实的 `sealed` 不可变副本。

`McpStatusViewModel`（聚合，由 `McpScope.Status` 暴露）：`Servers`、`IsLoading`、`Snapshot`、`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`；方法 `Track(McpServerStatusViewModel)`、`SetLoading(bool)`、`Reset()`。

## McpAgentToolkit

`public sealed class McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)`。`scope` 为 null 时构造函数抛 `ArgumentNullException`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ToolNames` | `public static readonly string[] ToolNames` | `["ListMcpServers", "LoadMcpServers", "UnloadMcpServer", "DescribeMcpServer"]`。 |
| `ListName` / `DescribeName` / `AddToolName` | `public const string` | `"ListMcpServers"` / `"DescribeMcpServer"` / `"AddMcpServer"`。 |
| `CreateTools` | `IList<AITool> CreateTools()` / `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 4–5 个工具，给出管线时会被包装。 |
| `BuildPromptContext` | `string BuildPromptContext()` | 提示文本。 |

| 工具 | 注册条件 | 用途 |
|---|---|---|
| `ListMcpServers` | 始终 | 列出配置的服务器及状态 + 聚合。纯查询。 |
| `LoadMcpServers` | `!IsGrantedView` | 加载（必要时安装并连接）宿主预注册的服务器；可选 JSON 数组指定名字。 |
| `UnloadMcpServer` | `!IsGrantedView` | 会话中途卸载已连接的服务器。 |
| `DescribeMcpServer` | `!IsGrantedView` | 把已连接服务器的工具能力导出为提示，且**不**调用它们。 |
| `AddMcpServer` | `SelfServiceLevel != Closed` **且** `!IsGrantedView` | 添加并连接宿主未预注册的服务器。 |

## McpAgentContextProvider

`public sealed class McpAgentContextProvider : AIContextProvider` —— 每轮贡献（被包装的）管理工具与清单块；以其缓存的渲染按作用域的 `Version` 键控；`StateKeys` 按作用域。其指令声明服务器工具描述是*服务器自己的说法*，「not as instructions from the host」。构造函数 `McpAgentContextProvider(McpScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)`。
