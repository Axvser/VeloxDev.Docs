# 派发工具

`VeloxDev.AI.SubAgents.SubAgentAgentToolkit` 是 `SubAgentScope` 面向智能体的视图：派发后台子代理、等待它、读取它的结论、查看名册、取消一个。

## 类：SubAgentAgentToolkit

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `SubAgentAgentToolkit(SubAgentScope scope, WorkflowAgentScope host)` | 把工具绑定到子系统与宿主作用域，后者的策略与预算适用。 |
| `ToolNames` | `static readonly string[] ToolNames` | `["SpawnSubAgent", "WaitSubAgents", "GetSubAgentResult", "ListSubAgents", "CancelSubAgent"]`。 |
| `CreateAllTools()` | `IList<AITool> CreateAllTools()` | 所有工具，忽略宿主的开关。用于列出可开关表面的 UI。 |
| `CreateTools()` | `IList<AITool> CreateTools()` | 工具未包装，省略宿主关闭的工具。 |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 工具已包装，每次调用被编组、预算化并上报。这是 provider 贡献的版本。 |

五个工具相对工作流图都是只读的，因此工作流宿主把它们排除在变更预算与脏标记之外。它们即使工作即时也是异步形状：`SpawnSubAgent` 返回句柄并在后台运行子代理，调用方绝不会在工具调用内等待子代理。

## 五个工具

| 工具 | 作用 |
|---|---|
| `SpawnSubAgent` | 启动一个子代理并立刻返回句柄。 |
| `WaitSubAgents` | 等待命名子代理或全部。超时是信息而非失败；报告 `timedOut: true` 并让子代理继续运行。 |
| `GetSubAgentResult` | 在子代理完成后读取其结果，受 `maxChars` 限制。 |
| `ListSubAgents` | 列出名册与每个子代理的状态。 |
| `CancelSubAgent` | 停止运行中的子代理；其状态变为 `Cancelled`，这不是错误。 |

## spawn 接受的字段

每个收窄字段都可选，且**省略字段意味着继承，而非没有**。空数组是请求「没有」，那是另一回事。

| 字段 | 效果 |
|---|---|
| `task` | 子代理的用户消息。必填。 |
| `name` | 名册标签；省略时用编号占位。 |
| `allowedTools` | 子代理可用的确切工具。 |
| `allowedSkills` | 子代理可读的技能；没有也会移除其技能工具。 |
| `allowedMcpServers` | 子代理可触及的 MCP 服务器。 |
| `maxToolCalls` / `maxReadToolCalls` / `maxWriteToolCalls` | 子代理的子限额。 |
| `allowNodeExecution` | 子代理能否运行节点业务代码。 |
| `allowedGenericCommands` | 子代理可调用的白名单命令名。 |
| `autoMarkDirty` | 子代理的变更是否把树标记为脏。 |
| `model` | 对本库不透明；交给宿主工厂。 |
| `notes` | 贡献到子代理简报的自由文本。 |

spawn 指定七个技能中的两个，子代理就得到那两个，其简报也会点名它们。其余五个不存在；若请求超出父级拥有，会作为 dropped 报告。

## 示例

```csharp
foreach (var name in SubAgentAgentToolkit.ToolNames)
    Console.WriteLine(name);
```

## 相关

- [SubAgentScope](../00_子智能体作用域/index.md) —— 这些工具驱动的子系统。
- [名册](../02_名册/index.md) —— 工具报告、面板绑定的内容。
- [上下文提供器](../03_上下文提供器/index.md) —— 这些工具从何处贡献。
