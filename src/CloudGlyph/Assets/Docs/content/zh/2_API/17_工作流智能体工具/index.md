# 工作流智能体工具

`WorkflowAgentScope` 把一棵工作流树变成 Microsoft Agent Framework 的工具面。内置工具覆盖检查、结构编辑、执行、布局、分析与状态；每次调用都被包装，因而会被计数、闸门拦截并通过作用域自己的管线上报。

作用域是其他所有智能体功能的入口。本页记录它面向工具的成员与工作流 toolkit；安全闸门、提示上下文、技能、MCP、子智能体与转录各自负责它们引入的成员。

## 命名空间

| 命名空间 | 类型 |
|---|---|
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope`、`WorkflowAgentToolkit`（经 `CreateToolkit`）、`WorkflowAgentSelectionExtensions`、`WorkflowStateTracker`、`WorkflowValidation`、`IWorkflowTreeValidator`、`WorkflowValidationIssue`、`AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`、`WorkflowToolCategory`、`CommandInvoker`、`CommandDescriptor`、`ComponentPatcher`、`TypeIntrospector` |
| `VeloxDev.AI` | `AgentToolCallEventArgs`、`IAgentToolCallNotifier`、`AgentClientExtensions`、`AgentObjectToolkit`、`AgentTelemetryExtensions` |

## 页面

- [WorkflowAgentScope](00_工作流作用域/index.md) —— 作用域的身份、工具注册、会话接线与 provider。
- [WorkflowAgentToolkit](01_工作流工具集/index.md) —— toolkit 与按分类列出的完整内置工具目录。
- [选择与状态](02_选择与状态/index.md) —— 面向提示的节点选择与快照/差异跟踪器。
- [验证与支持](03_验证与支持/index.md) —— 领域验证器、命令发现、JSON 补丁与类型 schema。
- [通用智能体扩展](04_通用智能体扩展/index.md) —— provider 挂载、通用对象 toolkit 与 OpenTelemetry 接线。

## 相关

- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 每次工具调用穿过的权限闸门与调用预算。
- [智能体上下文与技能](../19_智能体上下文与技能/index.md) —— 描述这些工具及其类型的提示文本。
- [MCP 集成](../20_MCP集成/index.md) —— 加入同一每轮工具集的外部工具。
- [子智能体](../21_子智能体/index.md) —— 继承此 toolkit 的派发工具。
- [智能体仪表盘与转录](../22_智能体仪表盘与转录/index.md) —— 观察工具做了什么。
