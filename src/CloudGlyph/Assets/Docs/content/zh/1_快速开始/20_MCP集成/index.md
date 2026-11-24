# MCP 集成

`McpScope` 负责连接智能体可以使用的 Model Context Protocol 服务器。服务器可以是经 npm、npx、uvx、pip、dotnet 或普通可执行文件启动的本地进程，也可以是走 Streamable HTTP 的远程端点。每个已连接服务器的工具都**每轮**加入智能体的工具集，所以装载或卸载会在下一轮生效，无需重建智能体。

scope 还贡献管理工具：列出、描述、装载、卸载、添加与重配服务器，以及读取它们的资源与提示模板。

## 你会构建什么

- 从 `{ "mcpServers": … }` 文档建立的 `McpScope`；
- 并排配置的一个本地 npx 服务器与一个远程 HTTP 服务器；
- 智能体用来操作它们的工具。

## 页面

- [安装准备](00_安装准备/index.md) —— 前置条件、包与第一个服务器。
- [使用](01_使用/index.md) —— 运行模式、装载、管理工具、状态视图模型与完整程序。

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
