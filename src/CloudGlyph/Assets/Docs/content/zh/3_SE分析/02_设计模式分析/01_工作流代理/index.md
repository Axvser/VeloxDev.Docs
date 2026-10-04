# 设计模式分析 —— 工作流代理

**workflow-agent** 让 LLM 通过 `Microsoft.Extensions.AI` 工具操控一棵活的 `IWorkflowTreeViewModel`。其模式表面是流式 **builder**（`WorkflowAgentScope`）、68 个 `AITool` 的 **facade**（`WorkflowAgentToolkit`）、包装每个工具的 **decorator**（`TrackedAIFunction`）、JSON 快照/差异的 **memento**（`WorkflowStateTracker`）、派发与 GUI 相同组件命令的 **command** 层（框架撤销/重做栈因此始终是唯一事实源）、到本地/远程 MCP 运行时的 **adapter**（`McpScope`）、**observer** 事件，以及 **strategy** 选择工具类别（`WorkflowToolCategory`）。

另外两个结构承载子系统层：

- 一条 **责任链** 管线（`AgentPipeline` → `TextPipeline` / `ToolPipeline` / 记账阶段），每次运行与每次工具调用都流经它；配一个 **带闸的装饰器**（`ToolPipeline.Refuse` / `Confirm`），触达每个切片 —— 内置、MCP、技能与子代理一视同仁。
- 一族 **收窄视图**：子代理派发、被授予的技能集与被授予的 MCP 服务器集都是父级的*过滤视图*，而非工具名列表 —— 因为一项携带自身重配置能力的权限无法用名字列表表达。

run/result 背后的执行工具（`RunCompiledWorkflow`、`GetNodeResult` 与运行句柄家族）镜像 GUI 编译路径：`CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` 驱动 `RuntimeEngine`，且路由器保持真实（选中兄弟分支意味着目标 NOT reached —— 不伪造取值）。安全由代码中的能力闸门（`WithAllowNodeExecution`、`WithAllowedGenericCommands`、`WithToolApproval`）强制执行，而非提示语。

## 页面

- [00 · 类图](00_类图/index.md) —— 作用域及其协作者
- [01 · 模式总览](01_模式总览/index.md) —— 一张表列出全部模式
- [02 · 构建者](02_构建者/index.md) —— `WorkflowAgentScope` 上的流式 `With*` 配置
- [03 · 门面](03_门面/index.md) —— 一个工具表面隐藏反射、命令派发与 JSON
- [04 · 装饰器](04_装饰器/index.md) —— `TrackedAIFunction` 包装每个 `AIFunction`
- [05 · 适配器](05_适配器/index.md) —— MCP 服务器（stdio/HTTP）暴露为 `AITool`
- [06 · 备忘录](06_备忘录/index.md) —— `WorkflowStateTracker` JSON 快照 + 属性级差异
- [07 · 命令](07_命令/index.md) —— 变更工具各派发一条组件命令
- [08 · 观察者](08_观察者/index.md) —— 管线事件与通知接口
- [09 · 策略](09_策略/index.md) —— `WorkflowToolCategory` 标志 + 交互处理器
- [10 · 子代理能力收窄](10_子代理能力收窄/index.md) —— 为何派发下传的是收窄*视图*而非工具名列表
- [11 · 子代理树与消耗计量](11_子代理树与消耗计量/index.md) —— 平坦名册投影成一棵树、调用向上记账 vs. token 自底向上聚合、以及重建闸
- [12 · 工具类别层级](12_工具类别层级/index.md) —— `WorkflowToolCategory` 标志与十个工具分组，含两个保留组
