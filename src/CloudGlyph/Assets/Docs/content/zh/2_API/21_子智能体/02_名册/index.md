# 名册

名册有两半，每半都有一个可绑定形式与一个线程安全形式。`SubAgentSummary` 是智能体调用读取的不可变副本；`SubAgentStatusViewModel` 是面板绑定的行。树是多个作用域扁平名册的投影。

## 页面

- [摘要与行](00_摘要与行/index.md) —— `SubAgentState`、`SubAgentSummary`、`SubAgentStatusViewModel`。
- [树](01_树/index.md) —— `SubAgentTreeViewModel` 与 `SubAgentTreeNodeViewModel`。

## 相关

- [SubAgentScope](../00_子智能体作用域/index.md) —— 名册的持有者。
- [派发工具](../01_派发工具/index.md) —— 创建子代理的工具。
