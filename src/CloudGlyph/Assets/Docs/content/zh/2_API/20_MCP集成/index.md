# MCP 集成

`McpScope` 负责连接智能体可以使用的 Model Context Protocol 服务器。服务器可以是经 npm、npx、uvx、pip、dotnet 或普通可执行文件启动的本地进程，也可以是走 Streamable HTTP 的远程端点。每个已连接服务器的工具都**每轮**加入智能体的工具集，所以装载或卸载会在下一轮生效，无需重建智能体。

scope 还贡献管理工具：列出、描述、装载、卸载、添加与重配服务器，以及读取它们的资源与提示模板。

## 命名空间

| 命名空间 | 类型 |
|---|---|
| `VeloxDev.AI.MCP` | `McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpConfigurationFile`、`McpServerStatus`、`McpServerStatusViewModel`、`McpStatusViewModel`、`McpServerSummary`、`McpAgentToolkit`、`McpAgentContextProvider` |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope.WithMcps`、`WorkflowAgentScope.Mcp` |

## 页面

- [McpScope](00_MCP作用域/index.md) —— 配置、装载、卸载、开关、状态与释放。
- [服务器配置](01_服务器配置/index.md) —— `McpServerConfiguration`、运行模式与 `.mcp.json` 解析。
- [服务器状态](02_服务器状态/index.md) —— 可绑定服务器行与聚合计数。
- [MCP 工具](03_MCP工具/index.md) —— 管理 toolkit 与上下文 provider。

## 工具从哪来

| 来源 | 由谁贡献 |
|---|---|
| 已连接服务器的工具 | MCP 上下文 provider，每轮 |
| `ListMcpServers`、`LoadMcpServers`、`UnloadMcpServer`、`AddMcpServer`…… | 同一个 provider |
| `ListMcpResources`、`ReadMcpResource`、`ListMcpPrompts`、`GetMcpPrompt` | 同一个 provider |

不要再 `WithTools` 注册一遍：框架会把工具列表做并集且不按名去重。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— MCP 工具与内置工具并排。
- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 为什么添加服务器属于 `Curate` 动作。
