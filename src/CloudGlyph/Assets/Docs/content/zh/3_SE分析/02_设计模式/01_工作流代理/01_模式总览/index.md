# 工作流代理 —— 模式总览

| 模式 | 位置 | 作用 |
|---|---|---|
| 建造者 | `WorkflowAgentScope` | 流式 `With*` 配置；每个方法返回同一作用域，并在真实变化时提升 `Version`。 |
| 外观 | `WorkflowAgentToolkit` | 一个 66 工具的分类表面（外加条件交互/计划工具）隐藏反射、命令派发与紧凑 JSON。 |
| 装饰器 | `TrackedAIFunction`（internal） | 包装每个 `AIFunction`，使调用被编组、闸控、计数并报告。 |
| 备忘录 | `WorkflowStateTracker` | JSON 快照 + 属性级差异，让模型看到变化而非全量状态。 |
| 命令 | Mutation 工具 | 每个派发恰好一条 `IWorkflow*ViewModel` 命令；撤销/重做归 Core 所有。 |
| 适配器 | `McpScope` / `McpAgentToolkit` | 本地（stdio）与远程（HTTP）MCP 服务器暴露为 `AITool`。 |
| 适配器 | `SkillScope` / `SkillAgentToolkit` | 内嵌与文件 Agent Skills 暴露为四个 `AITool`。 |
| 策略 | `WorkflowToolCategory` | `[Flags]` 掩码选择构建哪些工具分组。 |
| 策略 | 权限模式 | `AgentPermissionMode` + `AgentPermissionRule` 决定运行、询问或拒绝；两个交互处理器提供行为。 |
| 观察者 | `AgentPipeline` + 通知接口 | 运行/工具事件发布到阶段链；`ToolCalled` 在作用域上触发。 |
| 责任链 | `AgentPipeline` | `TextPipeline` → `ToolPipeline` → `AccountingStage`；阶段可为后续阶段丢弃事件。 |
| 中介者（闸门） | `ToolPipeline` | 每个作用域一份共享策略，在每个切片上执行预算、开关与权限。 |
| 收窄视图 | 子代理 spawn / 技能授予 / MCP 授予 | 自带重配置能力的权限以*过滤视图*下传，而不是名字列表。 |
| 组合账本（链） | `ToolCallLedger` | 子代理额度是父额度的一份；`Spend` 沿链行走，根看到整棵树。 |
| 惰性缓存（记忆化渲染） | `WorkflowAgentContextProvider` | 每轮渲染；没有变化时复用上一次渲染（乃至同一个 `AIContext`）。 |

## 子系统层的两个结构主题

1. **一个闸门，每个切片。** 预算、逐工具开关与权限策略（`Allow`/`Ask`/`Deny`）位于每个作用域一个 `ToolPipeline` 实例上，MCP 与技能提供器拿到的也是它。因此开关或 `Deny` 不可能在一条路径上生效、在另一条上被忽略。

2. **收窄永远是求交。** spawn 的工具列表、技能集、MCP 服务器集、预算上限、节点执行标志与脏标记模式，都与父作用域实际拥有的东西求交，被丢弃的项在 spawn 自己的结果中报告。父作用域按构造即为天花板。

> 各模式的图表与源码引用见对应子页。
