# 04 · 自定义工具与 MCP

## 1. 开发者注册的工具

```csharp
using Microsoft.Extensions.AI;

AIFunction ping = AIFunctionFactory.Create(() => "pong", "Ping");

scope.WithTools("用 Ping 检查连通性。", ping);     // 可变更的自定义工具
scope.WithQueryTools(null, lookupTool);            // 只读自定义工具
```

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` | 注册可变更的自定义工具；始终包含在 `ProvideTools()` 中。 |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` | 注册只读自定义工具 —— 永不自动标脏，永不计为写。 |

- `AIFunction` 自定义工具会被 `TrackedAIFunction` 包装，从而与内置工具一样获得 UI 线程编组、预算计数、`ToolCalled` 回调与自动脏标记。非 `AIFunction` 工具按原样加入，得不到上述任何一项。
- 可选的 `promptContext` 会作为「Custom Tools」小节注入提示。注册按组记忆，因此**子代理派发可以只授予子集**，并带上与之匹配的指引 —— 绝不会带上子代理未收到工具的指引。

**预期结果：** `scope.ProvideTools()` 中除 68 个内置工具外还包含你的工具名。

## 2. 挂载 MCP 服务器

`McpScope` 加载 Model Context Protocol 服务器，并把它们的工具并入 agent。宿主一次调用即可挂载该子系统；子系统每轮贡献自己的工具与提示文本。

```csharp
using VeloxDev.AI.MCP;

var mcp = new McpScope();
mcp.WithServers(new McpServerConfiguration
{
    Name = "Filesystem",
    RunMode = McpServerRunMode.Npx,
    Package = "@modelcontextprotocol/server-filesystem",
    Arguments = [AppContext.BaseDirectory],
});

scope.WithMcps(mcp);                 // 把子系统接进作用域
await mcp.LoadAsync(mcp.RegisteredServers);
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`Mcp`、`McpServers`、`LoadMcpServersAsync`）。

`WithMcps` 一次做四件事：把 MCP 作用域的确认处理器设为 workflow 作用域的 `ResolveConfirmationAsync`（审批只需配置一次），把 UI `SynchronizationContext` 交给它，并组合出 `mcp.CreateContextProvider(SharedTools, Pipeline)`，使 MCP 来源的工具加入与内置工具**相同**的预算、闸门与回调。

**预期结果：** `LoadAsync` 后，已连接服务器的工具出现在下一轮的工具列表中；卸载服务器会把它从下一轮移除。

## 3. MCP 管理工具

`McpAgentToolkit` 向模型暴露服务器管理。注册是有条件的：

| 工具 | 注册条件 |
|---|---|
| `ListMcpServers` | 始终 —— 纯查询 |
| `LoadMcpServers` | `!IsGrantedView`（即由宿主拥有该作用域，而非收窄的子代理视图） |
| `UnloadMcpServer` | `!IsGrantedView` |
| `AddMcpServer` | `SelfServiceLevel != McpSelfServiceLevel.Closed` **且** `!IsGrantedView` |

`McpSelfServiceLevel` 是一道阶梯：`Closed = 0`（demo 的选择 —— agent 只能加载/卸载/查看宿主预注册的服务器）、`RemoteConfirmed = 1`、`AllConfirmed = 2`、`Unrestricted = 3`。用 `McpScope.WithSelfService(level)` 提升。

**预期结果：** 在 `Closed` 下提供 `ListMcpServers` / `LoadMcpServers` / `UnloadMcpServer` / `DescribeMcpServer`，没有 `AddMcpServer`；提升级别后新增 `AddMcpServer`。

## 4. 运行模式与配置

| `McpServerRunMode` | 命令模型 |
|---|---|
| `Npm` | `npm install` 到 `{root}/node/{package}/`，然后 `node {entry} {args}`。 |
| `Npx` | `npx -y {package} {args}`（临时下载，不安装）。 |
| `Uvx` | `uvx {package} {args}`。 |
| `Dotnet` | `dotnet {dll} {args}`（用户预先发布到 `{root}/dotnet/`）。 |
| `Pip` | 创建 venv、`pip install`，然后 `python -m {module} {args}`。 |
| `Exe` | 直接执行 `{root}/exe/{package}`。 |
| `Http` | 连接 `Endpoint` 处的远程服务器（Streamable HTTP，SSE 回退）。 |

`McpServerConfiguration.Options` 是匿名对象 blob：`Http` 用 `headers`、`oauth`、`connectionTimeout`、`transportMode`、`ownsSession`；stdio 用 `env`、`workingDirectory`。未知键会被拒绝。

**预期结果：** 一个错误配置（未知 `Options` 键、本地模式缺 `Package`）只让该服务器失败 —— 其状态变为 `Error`，触发 `ServerError`，贡献零个工具；批次中的其余服务器照常加载。

## 5. 合在一起看

```csharp
scope.WithTools("用 Ping 检查连通性。", ping)
     .WithMcps(mcp);
```

**预期结果：** 下一轮的工具列表是内置工具加上 `Ping` 加上每个已加载服务器的工具，并且提示中带上自定义工具指引与 MCP 清单块。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。接线与条件化工具注册读自 `WorkflowAgentScope.WithMcps` 与 `McpAgentToolkit.CreateTools`；未从本页加载任何 MCP 服务器。（确定性 `Agent/**` 测试套件已通过 —— 见「工具预算与宿主策略」页 —— 但该套件不会启动真实的 MCP 服务器。）
