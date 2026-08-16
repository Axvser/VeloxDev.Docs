# Workflow Agent — 命名空间：`VeloxDev.AI.MCP`

### `McpScope`

本地 MCP 环境：安装服务器包并通过 stdio（或远程 HTTP）连接，返回工具为 `AITool[]`。

#### `WithMcpRoot`

**签名：** `public McpScope WithMcpRoot(string relativePath)`
**返回：** 同一个作用域。
**说明：** 根目录相对 `AppContext.BaseDirectory`；默认 `".evn/mcp"`。运行时子目录：`{root}/node/`（npm/npx）、`{root}/py/`（pip/uvx）、`{root}/dotnet/`、`{root}/exe/`。

#### `LoadAsync`

**签名：** `public async Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)`
**返回：** 所有已加载服务器工具组成的 `AITool[]`。
**异常：** 单服务器失败不抛出 —— 触发 `ServerError` 事件，该服务器贡献 0 个工具。取消时传播 `OperationCanceledException`。
**示例：** `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`，第 163-187 行；演示 `AgentHelper.LoadMcpServersAsync`。
**说明：** 本地模式（`Npm`/`Pip`）先安装（幂等，进程级 `s_installed` 集合 + `SemaphoreSlim`），再经 stdio 连接；`Npx`/`Uvx`/`Dotnet`/`Exe` 直接连接；`Http` 经 Streamable HTTP（SSE 回退）连接。状态实时驱动到 `Status`（`McpStatusViewModel`），注册了同步上下文时 marshal 到 UI 线程。

#### `ServerError`

**签名：** `public event Action<McpServerConfiguration, Exception>? ServerError`
**说明：** 服务器加载失败时触发；错误不重抛。该服务器状态变为 `McpServerStatus.Error`。

#### 其他成员

| 成员 | 签名 | 作用 |
|---|---|---|
| `McpRootRelative` | `string { get; }` | 当前 MCP 根（相对）。 |
| `Status` | `McpStatusViewModel { get; }` | 全局可绑定的逐服务器状态 + 聚合计数。 |
| `LoadedTools` | `IReadOnlyList<AITool> { get; }` | 所有已连接服务器工具的聚合；会话中途变化。 |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | 单台已连接服务器的工具（未连接返回空）。 |
| `UnloadServer` | `bool UnloadServer(string name)` | 移除某服务器工具并把状态重置为 `NotStarted`。 |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan?)` | 全局连接超时（Http 模式）。 |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext?)` | 把状态更新 marshal 到 UI 线程。 |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string>>)` | 远程服务器的 OAuth 授权重定向处理器。 |

### `McpServerConfiguration`

**签名：** `public partial class McpServerConfiguration`（MVVM 源生成属性）

| 属性 | 类型 | 描述 |
|---|---|---|
| `Name` | `string` | 服务器名（状态/工具键）。 |
| `Description` | `string` | 人类可读描述。 |
| `RunMode` | `McpServerRunMode` | 如何启动/到达服务器。 |
| `Package` | `string` | npm/PyPI 包名、`dotnet/` 下的 DLL 路径或 `exe/` 下的可执行路径。注意属性名是 **`Package`**，不是 `NpmPackage`。 |
| `Version` | `string?` | 版本标签（Npm/Pip）；`null` = `"latest"`。 |
| `Arguments` | `string[]` | 传给服务器进程的额外参数。 |
| `Endpoint` | `string?` | `Http` 模式的远程 URL。 |
| `Options` | `object?` | 匿名对象序列化；已知键 `headers`、`oauth`、`connectionTimeout`、`transportMode`、`ownsSession`、`env`、`workingDirectory`；未知键被拒绝。 |

### `McpServerRunMode`

`Npm`（npm install + node）、`Npx`（npx -y）、`Uvx`（uvx）、`Dotnet`（dotnet {dll}）、`Pip`（venv + pip install + python -m）、`Exe`（直接执行可执行文件）、`Http`（远程 Streamable HTTP/SSE）。旧版本文档列了六种模式；`Http` 是当前的第七种。

### `McpServerStatus`

`NotStarted`、`Installing`、`Connecting`、`Connected`、`Error`。

### `McpStatusViewModel` / `McpServerStatusViewModel`

可绑定的逐服务器状态（`Name`、`Description`、`RunMode`、`State`、`ToolCount`、`Error`、`Endpoint`，派生 `IsConnected`/`IsInstalling`/`IsConnecting`/`IsError`/`StateText`）与聚合 VM（`Servers`、`IsLoading`、`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`；`Track`、`SetLoading`、`Reset`）。

### `McpAgentToolkit`

Agent 可调用的 MCP 管理工具，经 `WorkflowAgentScope.WithTools(...)` 注册。

**签名：** `public sealed class McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)` —— `CreateTools()` 返回四个工具：

| 工具 | 用途 |
|---|---|
| `ListMcpServers` | 列出已配置服务器与状态（state、工具数、错误）+ 聚合计数。 |
| `LoadMcpServers` | 加载（需要时安装并连接）宿主预注册服务器，可传名称子集。 |
| `UnloadMcpServer` | 会话中途卸载已连接服务器。 |
| `DescribeMcpServer` | 导出已连接服务器的工具能力为提示词而不调用工具。 |

安全模型：服务器配置在加载时确定一次、之后不可变更；Agent 只能加载/卸载/查看，不能重新配置。
