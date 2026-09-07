# 工作流代理 — 命名空间：`VeloxDev.AI.MCP`

本地/远程 MCP 托管：`McpScope` 安装服务器包（npm/pip）、经 stdio 启动进程或经 Streamable HTTP（SSE 兜底）到达远程服务器，把每台服务器的工具作为 `AITool` 返回；`McpAgentToolkit` 把服务器管理变成 Agent 可调用的工具。以下类型均位于 `VeloxDev.AI.MCP`（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/MCP/`）。安全模型：服务器配置在加载时一次固定；Agent 只能加载/卸载/检查，绝不重新配置。

**证据：** **测试**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/MCP/*`）+ **Demo**（`AgentHelper` 的 `Mcp`/`McpServers` 与 `McpAgentToolkit` 注册）。

## McpScope

`public class McpScope`。管理 MCP 安装根与连接生命周期。`McpScope.McpRootRelative` 默认为 `".evn/mcp"`（相对 `AppContext.BaseDirectory`）；运行时位于 `{root}/node/`（npm/npx）、`{root}/py/`（pip/uvx）、`{root}/dotnet/`、`{root}/exe/`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ServerError` | `event Action<McpServerConfiguration, Exception>?` | 某服务器加载失败时触发；错误**不会**被重新抛出，该服务器贡献零个工具。 |
| `McpRootRelative` | `string { get; private set; }` | 当前 MCP 根（相对路径）。 |
| `Status` | `McpStatusViewModel { get; }` | 全局可绑定的每服务器状态 + 聚合，在 `LoadAsync` 期间实时驱动。 |
| `LoadedTools` | `IReadOnlyList<AITool> { get; }` | 所有已连接服务器的工具聚合；会随会话变化（卸载 → 工具消失）。 |
| `WithMcpRoot` | `McpScope WithMcpRoot(string relativePath)` | 设置安装根。 |
| `WithConnectionTimeout` | `McpScope WithConnectionTimeout(TimeSpan?)` | 全局连接/初始化超时（Http 模式）；单服务器覆盖经 `Options.connectionTimeout`。 |
| `WithSynchronizationContext` | `McpScope WithSynchronizationContext(SynchronizationContext?)` | 把所有状态更新封送到给定 UI 上下文。 |
| `WithOAuthAuthorizationRedirect` | `McpScope WithOAuthAuthorizationRedirect(Func<Uri, Uri, CancellationToken, Task<string?>>)` | 远程服务器的 OAuth 授权重定向处理器（打开 `authorizationUri`，返回携带授权码的最终重定向 URL）。未设置时使用 MCP SDK 的默认控制台输入处理器。 |
| `LoadAsync` | `Task<AITool[]> LoadAsync(IEnumerable<McpServerConfiguration> servers, CancellationToken ct = default)` | 依序加载服务器。 |
| `GetServerTools` | `IReadOnlyList<AITool> GetServerTools(string name)` | 某一已连接服务器的工具（未连接时为空）。 |
| `UnloadServer` | `bool UnloadServer(string name)` | 移除某服务器的工具集并将其状态重置为 `NotStarted`。返回是否曾有已加载工具。 |

**`LoadAsync` 行为。** `Npm`/`Pip` 先安装（幂等，进程级安装缓存 + `SemaphoreSlim`）再经 stdio 连接；`Npx`/`Uvx`/`Dotnet`/`Exe` 直接连接；`Http` 经 Streamable HTTP（SSE 兜底）连接。单服务器失败被捕获——状态变为 `McpServerStatus.Error`、触发 `ServerError`、该服务器贡献零个工具；调用方取消会传播。远程连接遵守 `WithConnectionTimeout` 并带宿主侧硬兜底。

## McpServerConfiguration

`public partial class McpServerConfiguration`——MVVM 源生成（`[VeloxProperty]`）属性。

| 属性 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 服务器名（状态/工具键）。 |
| `Description` | `string` | 人类可读描述。 |
| `RunMode` | `McpServerRunMode` | 服务器的启动/到达方式。 |
| `Package` | `string` | Npm/Npx/Uvx/Pip：包名；Dotnet：`dotnet/` 下的 DLL 路径（如 `"sharp-email-mcp/SharpEmailMcp.dll"`）；Exe：`exe/` 下的可执行文件路径。 |
| `Version` | `string?` | `Npm`/`Pip` 的版本标签；`null` = `"latest"`。 |
| `Arguments` | `string[]` | 传给服务器进程的额外参数。 |
| `Endpoint` | `string?` | `Http` 模式的远程 URL。 |
| `Options` | `object?` | 匿名对象 blob（见下）；未知键会被 `McpScope` 拒绝。 |

**`Options` 键。** Http：`headers`（额外头）、`oauth`（`clientId`、`clientSecret`、`redirectUri`、`scopes`——Authorization Code + PKCE）、`connectionTimeout`（秒或 TimeSpan 字符串；覆盖作用域级值）、`transportMode`（`AutoDetect`/`StreamableHttp`/`Sse`）、`ownsSession`。Stdio：`env`、`workingDirectory`。

## McpServerRunMode

`enum McpServerRunMode`——服务器的到达方式：

| 模式 | 命令模型 |
|---|---|
| `Npm` | `npm install` 到 `{root}/node/{package}/`，再 `node {entry} {args}`。 |
| `Npx` | `npx -y {package} {args}`（临时下载，不安装）。 |
| `Uvx` | `uvx {package} {args}`（uv 自带隔离环境）。 |
| `Dotnet` | `dotnet {dll} {args}`；用户需预发布到 `{root}/dotnet/{package}`。 |
| `Pip` | 在 `{root}/py/venvs/{package}/` 创建 venv，`pip install`，再 `python -m {module} {args}`。 |
| `Exe` | 直接执行 `{root}/exe/{package}`（技术无关）。 |
| `Http` | 经 `Endpoint` 连接远程服务器（Streamable HTTP，SSE 兜底）；不启动本地进程。 |

## McpServerStatus

`enum McpServerStatus`——连接生命周期：`NotStarted`、`Installing`（仅本地 npm/pip；Http 跳过此状态）、`Connecting`、`Connected`、`Error`。

## 状态视图模型

`McpServerStatusViewModel`（单服务器）：`Name`、`Description`、`RunMode`、`State`、`ToolCount`、`Error`、`Endpoint`，外加派生 `IsConnected`/`IsInstalling`/`IsConnecting`/`IsError` 与中文 `StateText`（`已连接`/`安装中`/`连接中`/`错误`/`未启动`）。

`McpStatusViewModel`（聚合，由 `McpScope.Status` 暴露）：`Servers`、`IsLoading`、`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`；方法 `Track(McpServerStatusViewModel)`、`SetLoading(bool)`、`Reset()`。

## McpAgentToolkit

`public sealed class McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)`——Agent 可调用的 MCP 管理工具；经 `WorkflowAgentScope.WithTools(...)` 注册（Demo `AgentHelper.ProvideAgent`）。构造时 `scope` 为 null 抛 `ArgumentNullException`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools()` | 四个工具：`ListMcpServers`、`LoadMcpServers`、`UnloadMcpServer`、`DescribeMcpServer`。 |

| 工具 | 用途 |
|---|---|
| `ListMcpServers` | 列出已配置服务器与状态（`runMode`、`state`、`stateText`、`toolCount`、`error`）+ 聚合计数。纯查询。 |
| `LoadMcpServers` | 加载（需要时先安装并连接）宿主预注册的服务器；可选 JSON 数组只加载指定服务器名的子集。 |
| `UnloadMcpServer` | 会话中卸载某已连接服务器（工具从下一次会话消失；状态重置为 `NotStarted`）。 |
| `DescribeMcpServer` | 把某已连接服务器的工具能力（名称 + 描述）导出为提示词，**不**实际调用它们。 |
