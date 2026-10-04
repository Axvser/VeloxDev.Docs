# 工作流代理 —— 模式总览

| 模式 | 位置 | 作用 |
|---|---|---|
| Builder | `WorkflowAgentScope` | 流式 `With*` 配置；每个方法返回同一作用域，真实变化时推进 `Version`。 |
| Facade | `WorkflowAgentToolkit` | 一个 68 工具表面隐藏反射、命令派发与紧凑 JSON。 |
| Decorator | `TrackedAIFunction`（internal） | 包装每个 `AIFunction`，使调用被编组、闸控、计数与报告。 |
| Memento | `WorkflowStateTracker` | JSON 快照 + 属性级差异，让模型看到变化而非全量状态。 |
| Command | 变更工具 | 每个恰好派发一条 `IWorkflow*ViewModel` 命令；撤销/重做归 Core 所有。 |
| Adapter | `McpScope` / `McpAgentToolkit` | 本地（stdio）与远程（HTTP）MCP 服务器暴露为 `AITool`。 |
| Adapter | `SkillScope` / `SkillAgentToolkit` | 内嵌与文件 Agent Skills 暴露为四个 `AITool`。 |
| Strategy | `WorkflowToolCategory` | 一个 `[Flags]` 掩码选择构建哪些工具分组。 |
| Strategy | 交互处理器 | `WithInteractionSafety` 级别 0–3 选择策略；两个处理器插入行为。 |
| Observer | `AgentPipeline` + 通知接口 | 运行/工具事件发布到阶段链；`ToolCalled` 在作用域上触发。 |
| 责任链 | `AgentPipeline` | `TextPipeline` → `ToolPipeline` → `AccountingStage`；阶段可为其后阶段丢弃事件。 |
| 中介（闸门） | `ToolPipeline` | 每个作用域一份共享策略，跨所有切片执行预算、开关与审批。 |
| 收窄视图 | 子代理派发 / 技能授予 / MCP 授予 | 携带自身重配置能力的权限以*过滤视图*而非名字表下传。 |
| 复合账本（链） | `ToolCallLedger` | 子代理的额度是父级的一份；`Spend` 沿链上行，根看到整棵树。 |
| 惰性缓存（记忆化渲染） | `WorkflowAgentContextProvider` | 逐轮渲染，未变化时复用上一次渲染（乃至同一个 `AIContext`）。 |

## 子系统层的两个结构主题

1. **一道闸门，每个切片。** 预算、逐工具开关与工具审批都活在每个作用域一份的 `ToolPipeline` 上，既被内置工具使用，也交给 MCP 与技能提供器。因此开关不可能在一条路径上生效而在另一条上被忽略。

2. **收窄永远是求交。** 派发的工具列表、技能集、MCP 服务器集、预算上限、节点执行标志与脏标记模式，各自都与父级实际持有的东西求交，被丢弃的都在派发自身结果中回报。父级按构造即天花板。

> 各模式的图与源码引用见对应子页面。
