# 子智能体

`SubAgentScope` 让智能体派出后台子代理。每个子代理都是同一棵树上的完整工作流智能体，持有父级能力的一个切片。派发方式是**派出后轮询**：spawn 立刻返回句柄，子代理在句柄后面运行——因为 spawn 发生在宿主线程上的一次工具调用里。

子代理的额度是父级账本的一份份额，不是另一口锅。这正是无限深度能够终止的原因，也是根上限就是整棵树上限的原因。

## 命名空间

| 命名空间 | 类型 |
|---|---|
| `VeloxDev.AI.SubAgents` | `SubAgentScope`、`SubAgentAgentToolkit`、`SubAgentAgentContextProvider`、`SubAgentState`、`SubAgentSummary`、`SubAgentStatusViewModel`、`SubAgentTreeViewModel`、`SubAgentTreeNodeViewModel` |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope.WithSubAgents`、`WorkflowAgentScope.SubAgents` |

## 页面

- [SubAgentScope](00_子智能体作用域/index.md) —— 创建、深度、预算、名册与释放。
- [派发工具](01_派发工具/index.md) —— 五个面向模型的工具与 spawn 接受的字段。
- [名册](02_名册/index.md) —— 状态行、不可变摘要与可绑定树。
- [上下文提供器](03_上下文提供器/index.md) —— 子系统如何把自己贡献到一轮调用。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 子代理继承的工具。
- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 整棵树消耗的预算。
