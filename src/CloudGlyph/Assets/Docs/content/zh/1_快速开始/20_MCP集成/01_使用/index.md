# 使用

## 运行模式

| `McpServerRunMode` | 启动方式 |
|---|---|
| `Npm` | 安装包，再用 Node 运行 |
| `Npx` | `npx -y <package> <args>`——不安装 |
| `Uvx` | `uvx <package> <args>`——隔离的 Python 环境 |
| `Pip` | 建 venv、`pip install`、再运行模块 |
| `Dotnet` | `dotnet <dll> <args>` |
| `Exe` | 直接运行 `<mcpRoot>/exe/<Package>` |
| `Normal` | 原样运行 `Package`，`Arguments` 逐字传入 |
| `Http` | 通过 Streamable HTTP 连接 `Endpoint`，回退 SSE |

本地安装隔离在 `.evn/mcp/{runtime}/` 下。`Normal` 没有安装步骤，也不加根前缀；命令由操作系统解析。

**预期结果：** `Package = "node"`、`Arguments = ["server.js"]` 的 `Normal` 服务器原样执行这条命令。

## 装载、替换与增量添加

```csharp
var tools = await mcp.LoadAsync(mcp.RegisteredServers); // 替换先前装载的一切
```

`LoadAsync` 会释放它替换掉的客户端，旧的 stdio 子进程不会活过一次重新装载。`AddAsync` 是增量版本：

```csharp
var extraTools = await mcp.AddAsync(new McpServerConfiguration
{
    Name = "Local tools",
    RunMode = McpServerRunMode.Normal,
    Package = "node",
    Arguments = ["server.js", "--port", "0"],
});
```

两者都会记住配置，因此智能体的 `LoadMcpServers` 之后可以按名把它带回来。

**预期结果：** `LoadAsync` 两个服务器后，`mcp.LoadedTools` 包含它们的工具，`mcp.Status.Servers` 有两条跟踪记录。

## 读取 `.mcp.json`

```csharp
var configs = McpConfigurationFile.Load(".mcp.json");   // 或 Parse(json)
mcp.WithServersFromFile(".mcp.json");                   // 预注册，之后按名装载
await mcp.LoadConfigurationFileAsync(".mcp.json", ct);  // 立刻装载（替换语义）
```

`command` 条目变成 `Normal` 并保留参数；`url` 条目变成 `Http`；`env`、`cwd`、`headers` 与 `type: "sse"` 映射进 `Options`；`disabled: true` 的条目被跳过。`${VAR}` 与 `${VAR:-default}` 从进程环境展开。

**预期结果：** 一个含 `command`、`url`、`disabled` 各一条的文档，最终注册两个服务器。

## 管理工具

`mcp.CreateContextProvider()` 每轮贡献这些工具：

| 工具 | 分类 | 用途 |
|---|---|---|
| `ListMcpServers` | Read | 服务器状态与工具数 |
| `DescribeMcpServer` | Read | 导出服务器的工具能力提示 |
| `ListMcpResources` / `ReadMcpResource` | Read | MCP 资源 |
| `ListMcpPrompts` / `GetMcpPrompt` | Read | MCP 提示模板 |
| `LoadMcpServers` / `UnloadMcpServer` | Curate | 安装/连接或拆除 |
| `AddMcpServer` / `SetMcpServerArguments` | Curate | 添加或重配服务器 |

把它接到工作流 scope，同一批工具就受该 scope 的预算与权限策略管辖：

```csharp
var scope = tree.AsAgentScope()
    .WithMcps(mcp)
    .WithPermissionMode(AgentPermissionMode.AutoEdit);
```

`AutoEdit` 下装载服务器（`Curate`）会询问宿主的确认处理器；`Bypass` 下不问，但 `category:Curate` 的 `Deny` 规则仍然成立。

**预期结果：** 模型在下一轮看到 `ListMcpServers` 与 `LoadMcpServers`，不需要重建。

## 按服务器与按工具开关

```csharp
mcp.SetServerEnabled("Filesystem (npx)", false);
mcp.SetToolEnabled("Microsoft Learn", "microsoft_docs_search", false);
```

被禁用的服务器保留连接与状态，但不贡献工具；被禁用的工具会从该服务器的工具列表里过滤掉。两个开关都会推进 `Version`，下一轮提示词会反映变化。

**预期结果：** `mcp.IsServerEnabled("Filesystem (npx)")` 为 `false`，它的工具从 `LoadedTools` 中消失。

## 状态视图模型

`mcp.Status` 可绑定；设置了 `SynchronizationContext` 时更新会编组到 UI 线程：

- 每服务器：`Name`、`StateText`（`NotStarted` / `Installing` / `Connecting` / `Connected` / `Error`）、`ToolCount`、`Error`；
- 聚合：`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`。

非 UI 线程请读 `mcp.Status.Snapshot`（不可变副本），而不是 `Servers`。

**预期结果：** 服务器连接期间 `WorkingCount` 为 `1`；连接完成后 `ConnectedCount` 为 `1`。

## 验证

1. 运行完整程序。它打印两个已注册服务器，以及点名二者的清单块。
2. 确认被禁用的条目没有出现。
3. 有网络时调用 `await mcp.LoadAsync(new[] { learn })`，检查 `Status.Servers[0].StateText` 到达 `Connected`；无网络时会到 `Error`，消息说明原因。

## 完整代码

```csharp
using VeloxDev.AI.MCP;

const string document = """
{
  "mcpServers": {
    "learn": {
      "url": "https://learn.microsoft.com/api/mcp"
    },
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/data"]
    },
    "disabled-example": {
      "command": "node",
      "args": ["server.js"],
      "disabled": true
    }
  }
}
""";

var configs = McpConfigurationFile.Parse(document);
var mcp = new McpScope().WithServers(configs.ToArray());

Console.WriteLine($"registered: {mcp.RegisteredServers.Count}");
foreach (var server in mcp.RegisteredServers)
    Console.WriteLine($"  {server.Name} ({server.RunMode})");

Console.WriteLine();
Console.WriteLine(mcp.BuildInventoryBlock());
```

**预期输出形态：**

```text
registered: 2
  learn (Http)
  files (Normal)

# MCP Servers
… 点名 learn 与 files 的清单文本 …
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`、`McpConfigurationFile.cs`、`McpServerConfiguration.cs`、`McpServerRunMode.cs`、`McpAgentToolkit.cs`、`McpStatusViewModel.cs`，以及 `Src/Core/VeloxDev.Core.Extension/README.md` 中的用法说明做了静态核对。连接实时服务器需要网络，因此没有记录运行输出。
