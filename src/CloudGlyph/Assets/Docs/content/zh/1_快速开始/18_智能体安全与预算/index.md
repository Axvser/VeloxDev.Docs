# 智能体安全与预算

工作流智能体可以编辑图、运行节点业务代码、安装 MCP 服务器。`VeloxDev.AI.Safety` 在每次调用时决定它能不能做。这个决定是一个**有名字的模式**加一组**规则**，并且在调用点强制执行，而不只是写在提示词里——所以切换模式会直接管住下一次工具调用。

同一个包还负责每一次调用要消耗的**预算**：总调用数、读调用数、写调用数、token 与结果大小。

## 你会构建什么

- 一个 `AgentPermissionPolicy`，以及五个动作分类各自的决策表；
- 比任何模式都更严的规则，其中一条 `Deny` 在 `Bypass` 下仍然成立；
- 一个配置了模式、规则、judge 与调用预算的 scope。

## 页面

- [安装准备](00_安装准备/index.md) —— 前置条件、包与第一条策略。
- [使用](01_使用/index.md) —— 模式矩阵、规则写法、judge、预算语义与完整程序。

## 两个层次

| 层次 | 是什么 | 能否比模式更严 |
|---|---|---|
| `AgentPermissionMode` | 用户能命名和切换的粗粒度状态 | —— |
| `AgentPermissionRule` | 带 `Allow` / `Ask` / `Deny` 的模式 | 能，包括在 `Bypass` 下 |

`AgentActionCategory` 是**调用期分类**（`Read`、`Edit`、`Execute`、`Curate`、`Interact`）。它刻意不是 `WorkflowToolCategory`——后者只是决定哪些工具送给模型的工具面过滤器。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 这些规则管辖的工具面。
- [MCP 集成](../20_MCP集成/index.md) —— 模式最谨慎对待的 `Curate` 调用。
