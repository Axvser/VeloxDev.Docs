# MCP 工具

MCP 子系统通过一个管理 toolkit 与一个上下文 provider 到达模型。toolkit 的名称是公共常量，因此组合多个工具来源的宿主无需重复字面量即可分类它们。

## 类：McpAgentToolkit

`VeloxDev.AI.MCP.McpAgentToolkit` 是智能体可调用的 MCP 管理工具集。服务器配置由宿主预先提供；智能体不构造任意配置。安全边界与工作流工具一致：*宿主注册，智能体操作*。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)` | 在作用域及其可装载配置之上构建工具。 |
| `CreateTools()` | `IList<AITool> CreateTools()` | 管理工具，未包装。 |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 工具已包装，每次调用被编组、闸控并上报。这是 provider 贡献的版本。 |
| `BuildPromptContext()` | `string BuildPromptContext()` | 描述这些工具的提示文本。因为授权视图看到不同表面，故为生成式。 |
| `ToolNames` | `static readonly string[]` | 所有管理工具名，按注册顺序。 |
| `ReadToolNames` | `static readonly string[]` | 只读取的名称；宿主把它们分类为查询。 |

### 工具名常量

| 常量 | 值 |
|---|---|
| `ListName` | `ListMcpServers` |
| `LoadName` | `LoadMcpServers` |
| `UnloadName` | `UnloadMcpServer` |
| `DescribeName` | `DescribeMcpServer` |
| `AddToolName` | `AddMcpServer` |
| `SetArgumentsName` | `SetMcpServerArguments` |
| `ListResourcesName` | `ListMcpResources` |
| `ReadResourceName` | `ReadMcpResource` |
| `ListPromptsName` | `ListMcpPrompts` |
| `GetPromptName` | `GetMcpPrompt` |
| `LocalKind` | `mcp-add:local` |
| `HttpKind` | `mcp-add:http` |

`LocalKind` 与 `HttpKind` 是当决定取决于参数而非工具时宿主编写规则所用的名称：一个会在机器上安装软件，另一个只把数据发出去。

### 每个工具做什么

| 工具 | 分类 | 用途 |
|---|---|---|
| `ListMcpServers` | Read | 服务器状态与工具数。 |
| `DescribeMcpServer` | Read | 导出服务器的工具能力提示。 |
| `ListMcpResources` / `ReadMcpResource` | Read | MCP 资源。 |
| `ListMcpPrompts` / `GetMcpPrompt` | Read | MCP 提示模板。 |
| `LoadMcpServers` / `UnloadMcpServer` | Curate | 安装/连接或拆除。 |
| `AddMcpServer` / `SetMcpServerArguments` | Curate | 添加或重配服务器。 |

添加与重配始终被提供；调用是否运行由会话权限模式与宿主规则在调用时决定。**授权视图**——交给被派发子智能体的表面——只注册 `ReadToolNames`，因为子智能体在父级回合挂起时运行，不得安装或拆除软件。

## 类：McpAgentContextProvider

`VeloxDev.AI.MCP.McpAgentContextProvider : AIContextProvider` 在每次调用时贡献作用域状态：服务器清单、管理工具与每个已连接服务器的工具。它让 MCP 在没有工作流层时也可用。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `McpAgentContextProvider(McpScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 为作用域创建 provider。独立使用可省略 `tools`。 |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | provider 的状态键。 |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | 渲染并贡献 MCP 状态。 |

渲染基于作用域 `Version` 缓存。MCP 没有语言维度，因此版本就是整个缓存键。装载、添加或卸载服务器会推进它，因此变化在下一轮到达模型而无需重建智能体。

## 说明

`McpToolProxy` 与 `HostedMcpServer` 是内部连接管线，不属于公共表面。用 `McpScope.LoadedTools`、`GetServerTools` 与状态视图模型观察连接。

## 相关

- [McpScope](../00_MCP作用域/index.md) —— 这些工具操作的作用域。
- [服务器状态](../02_服务器状态/index.md) —— 读取工具报告的状态。
- [智能体安全与预算](../../18_智能体安全与预算/index.md) —— `Curate` 闸门。
