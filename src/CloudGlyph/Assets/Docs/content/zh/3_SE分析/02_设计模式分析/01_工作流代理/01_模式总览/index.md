# Workflow Agent — 设计模式 — 模式概览

工作流代理功能组合经典模式，使 LLM 可以操作一张 GUI 绑定的工作流树而不绕过其不变式。

| # | 模式 | 位置 | 如何体现 |
|---|---|---|---|
| 1 | **构建者** | `WorkflowAgentScope` | 流式 `With*` 方法返回 `this`；链末端物化为提示词与工具（`ProvideProgressiveContextPrompt()` / `ProvideTools()`）。 |
| 2 | **门面** | `WorkflowAgentToolkit` | 约 60 个 `AITool` 通过一个门面暴露完整的图控制，隐藏反射、命令派发与 JSON 格式化。 |
| 3 | **装饰器** | `TrackedAIFunction` | 一个 `DelegatingAIFunction` 包装器加入 UI 线程 marshal、调用计数、最大调用强制、`ToolCalled` 回调与可选自动置脏。 |
| 4 | **适配器** | `McpScope` | 把外部 MCP 运行时（stdio 进程或远程 HTTP）适配成 `AITool` 实例——本地安装、传输、JSON-RPC 握手、按服务器的 `ServerError` 隔离。 |
| 5 | **备忘录** | `WorkflowStateTracker` | `TakeSnapshot` 存储 JSON 快照；`GetChangesSinceLastSnapshot` 计算属性级差异——Agent 无需重读完整状态即可观察变化。 |
| 6 | **命令** | 变更 + 执行工具 | 每个工具恰好派发一个组件命令（`SetAnchorCommand`、`CreateNodeCommand`、`DeleteCommand`、……）并等待真实完成，因此框架撤销/重做栈是唯一真相源。 |
| 7 | **观察者** | `ToolCalled` / `ServerError` 事件 | `WorkflowAgentScope.ToolCalled` 在每次工具调用后通知；`McpScope.ServerError` 通知服务器加载失败（错误不重抛）。 |
| 8 | **策略** | `WorkflowToolCategory` + 交互处理器 | `CreateTools(categories)` 选择暴露哪些工具组；`WithSelectionHandler`/`WithConfirmationHandler` 注入宿主的交互策略，且仅当存在处理器且安全级别 > 0 时才注册对应工具。 |

## 能力门与交互安全

工具表面并非仅靠描述限制。`WithAllowNodeExecution` 门控节点执行工具（`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow`、`GetNodeResult`）；`WithAllowedGenericCommands` 对通用命令工具做白名单；每个被门控的工具在禁用时返回结构化 `{"status":"error"}`。`WithInteractionSafety(0-3)` 决定 Agent 通过 `RequestSelection` / `RequestConfirmation` 暂停询问的急切程度，`ResolveConfirmationAsync` 把 `AllowAlways` 批准按 `operationKey` 缓存到会话级（`WorkflowAgentScope.cs`，第 214-254、429-442 行）。

## 编译执行模型（Root vs Terminal）

run/result 工具镜像 GUI 编译路径，而非临时逐个执行节点：

- `RunCompiledWorkflow` 以 `CompileRole.Root` 编译从起始节点可达的子图，交由 `RuntimeEngine` 驱动整条链（路由器通过 `ICompileTimeRouter` 选分支）。
- `GetNodeResult` 以 `CompileRole.Terminal` 编译节点的祖先锥（反向编译）。锥内路由器保持**真实**分支语义：若路由器在运行时选中兄弟分支，目标**未到达**——工具返回显式 `error`（点名目标：`... was NOT reached ... No result was produced.`）且无数据（`WorkflowAgentToolkit.cs`，第 1789-1801、1827-1836 行）。绝不从兄弟分支伪造值。

上述一切的 **Agent 面向规范**都写在**双语内嵌提示文档**中（`Resources/Workflow/{en,zh}/{References,Safety,Skills}/*.md`，由 `AgentEmbeddedResources` 加载）——如 `CommandReference.md`、`CompilerUsage.md`、`Level1-3.md`——它们被注入系统提示词，是工具语义的权威描述。
