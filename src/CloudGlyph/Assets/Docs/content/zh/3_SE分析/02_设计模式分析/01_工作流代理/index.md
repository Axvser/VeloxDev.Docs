# 设计模式 — 工作流代理

**工作流代理**功能让 LLM 通过 `Microsoft.Extensions.AI` 工具操作一张活动的 `IWorkflowTreeViewModel`。其模式表面是：流畅**构建者**（`WorkflowAgentScope`）、约 60 个 `AITool` 的**门面**（`WorkflowAgentToolkit`）、包装每个工具的**装饰器**（`TrackedAIFunction`）、提供 JSON 快照/差异的**备忘录**（`WorkflowStateTracker`）、派发与 GUI 完全相同的组件命令的**命令**层（因此框架撤销/重做栈保持唯一真相源）、把远程/本地 MCP 运行时适配成工具的**适配器**（`McpScope`）、**观察者**事件，以及**策略**选定的工具类别。

run/result 背后的执行工具（`RunCompiledWorkflow`、`GetNodeResult`）镜像 GUI 编译路径：`CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` 驱动 `RuntimeEngine`，且路由器保持真实语义（选中兄弟分支意味着目标**未到达**——不伪造任何值）。安全性由代码中的能力门控制（`WithAllowNodeExecution`、`WithAllowedGenericCommands`），而非仅仅靠提示词描述。

## 页面

- [00 · 类图](00_class-diagram/index.md) — 代理作用域 / 工具包 / 状态追踪器 / MCP + 编译执行类
- [01 · 模式概览](01_patterns-overview/index.md) — 全部八个模式一览表
- [02 · 构建者](02_构建者/index.md) — `WorkflowAgentScope` 上的流畅 `With*` 配置
- [03 · 门面](03_门面/index.md) — 单一工具表面隐藏反射、命令派发与 JSON
- [04 · 装饰器](04_装饰器/index.md) — `TrackedAIFunction` 包装每个 `AIFunction`
- [05 · 适配器](05_适配器/index.md) — MCP 服务器（stdio/HTTP）暴露为 `AITool`
- [06 · 备忘录](06_备忘录/index.md) — `WorkflowStateTracker` JSON 快照 + 属性级差异
- [07 · 命令](07_命令/index.md) — 变更工具各自恰好派发一个组件命令
- [08 · 观察者](08_观察者/index.md) — `ToolCalled` / `ServerError` 事件
- [09 · 策略](09_策略/index.md) — `WorkflowToolCategory` 旗标 + 交互处理器
