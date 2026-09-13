# 工作流代理 — 快速入门

工作流代理（workflow-agent）特性是 VeloxDev 的 AI 控制层。它把一个运行中的工作流树（`IWorkflowTreeViewModel`，也就是工作流系统快速入门构建的那个对象）变成 LLM 可以通过函数调用工具驱动起来的表面：

- `tree.AsAgentScope()` 返回流式的 `WorkflowAgentScope` 构建器。它收集提示词语言、输出语言、类型发现、工具调用预算、主机策略门禁、交互安全、回调与自定义工具。
- `scope.ProvideProgressiveContextPrompt()` 生成系统提示词（渐进式披露让其保持精简）；`scope.ProvideAllContexts()` 生成完整自包含的版本。两者都会自动内嵌 `Resources/Workflow/{en,zh}` 下的**双语提示词文档**（`References`、`Skills`、`Safety`），让代理从同一批文档中学习框架规则。
- `scope.ProvideTools()` 返回 `WorkflowAgentToolkit` 的工具集：默认 60 个内置 `AITool`（注册交互工具后最多 62 个），按 `WorkflowToolCategory` 分组 —— Query、State、Mutation、Execution、Command、Graph、Layout、Analytics、Composite、Interaction。
- 执行在**三个层级**暴露，每层都有运行工具与仅编译计划工具：
  - **节点级** — `ExecuteNode` / `ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`（驱动单个节点的 `ReceiveCommand` / 广播命令，不编译）。
  - **链级（Root）** — `RunCompiledWorkflow(nodeIndex, seed?)` 运行编译后的前向链；`CompileWorkflow(nodeIndex)` 仅编译计划。
  - **结果级（Terminal）** — `GetNodeResult(nodeIndex, seed?)` 从某个节点的祖先锥计算其值；`CompileNodeResult(nodeIndex)` 仅编译锥。
  - 编译/运行建立在 `CompilerViewModel.CompileAsync(component, CompileRole.Root | CompileRole.Terminal)` 与 `RuntimeEngine` 之上（命名空间 `VeloxDev.Core.WorkflowSystem.CompilerEx`）——这是现行引擎；代码里已没有 `CompilerEngine` / `CompileToAsync`。
- `WorkflowStateTracker` 对树做 JSON 快照并报告 `addedNodes/removedNodes/modifiedNodes` 差异，让代理用最少上下文观察变化。
- MCP 支持（`VeloxDev.AI.MCP`）：`McpScope` 加载 Model Context Protocol 服务器（`McpServerRunMode.Npx`、`Http` 等）并把它们的工具合并进每一轮对话；`McpAgentToolkit` 把主机预注册的服务器以 list/load/unload/describe 工具的形式交给代理。
- `VeloxDev.AI` 的反射工具（`AgentContextAttribute`、`AgentLanguages`、`AgentContextReader`、`AgentCommandDiscoverer`、`AgentMethodInvoker`、`AgentPropertyAccessor`、`AgentTypeResolver`、事件参数类型、`SlotSelectorsAttribute`）支撑类型注册表与这些工具。

## 快速入门 — 子页面

本特性的快速入门拆分为下列页面（逐步导向最后一页那个可运行的单文件程序）：

- [00 前置条件](00_前置条件/) — 支持目标、SDK/运行时、你必须提供的服务（树、`IChatClient`、可选 MCP 运行时）
- [01 安装依赖](01_安装依赖/) — 添加 `VeloxDev.Core.Extension` 及其传递的 AI 包
- [02 构建作用域](02_构建作用域/) — `AsAgentScope()` 流式表面：语言、自动发现、提示词提供器、工具获取
- [03 工具预算与宿主策略](03_工具预算与宿主策略/) — 交互安全 0–3、工具调用预算、节点执行与通用命令门禁、UI 线程与脏标记
- [04 自定义工具与MCP](04_自定义工具与MCP/) — `WithTools` / `WithQueryTools`、加载 MCP 服务器、经 `McpAgentToolkit` 的宿主预注册服务器
- [05 运行一轮对话](05_运行一轮对话/) — 把提示词 + 工具交给聊天客户端、会话、逐轮工具合并、回复与撤销
- [06 三种执行模型](06_三种执行模型/) — 节点级、Root 链级与 Terminal 结果级工具；仅编译计划；其下的编译引擎
- [07 终结点结果语义](07_终结点结果语义/) — `GetNodeResult` / `CompileNodeResult`：祖先锥、真实 `BranchSegment` 路由、`targetReached` 契约与恢复
- [08 验证与完整代码](08_验证与完整代码/) — 演示与测试覆盖、可运行的单文件程序、运行声明
