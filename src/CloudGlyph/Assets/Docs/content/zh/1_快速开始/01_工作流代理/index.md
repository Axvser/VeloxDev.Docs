# 工作流代理 —— 快速开始

**workflow-agent** 是 VeloxDev 的 AI 控制层。它把一棵活的 workflow 树（一个 `IWorkflowTreeViewModel`，即「工作流系统」快速开始所构建的同一对象）变成一个 LLM 可通过函数调用工具来驱动的表面。

- `tree.AsAgentScope()` 返回流式的 `WorkflowAgentScope` 构建器。它收集提示语言、输出语言、类型发现、工具调用预算、宿主策略闸门、交互安全、回调与自定义工具。
- `scope.ProvideProgressiveContextPrompt()` 产出精简的系统提示；`scope.ProvideAllContexts()` 产出完整的自包含版本。两者都会内嵌 `Resources/Workflow/{en,zh}` 下的双语提示文档（`References`、`Skills`、`Safety`）。
- `scope.CreateContextProviders()` 返回每轮调用的提供器。**`WorkflowAgentContextProvider` 是每轮工具与指令的唯一来源**，因此挂载、关闭或加载某样东西，下一轮就能到达模型，无需重建 agent。
- 默认工具集是 **68 个内置 `AITool`**，按 `WorkflowToolCategory` 分组 —— Query(20)、State(3)、Mutation(23)、Execution(12)、Command(2)、Graph(5)、Layout(保留)、Analytics(1)、Composite(保留)、Interaction(至多 2，仅在配置了处理器且安全级别 > 0 时注册)，外加一个始终存在的预算工具 `ResetToolCallLimit`。
- 执行分为 **三层**，每层都有运行工具与只编译的计划工具：
  - **节点层** —— `ExecuteNode` / `ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`（单个节点的 `ReceiveCommand` / 广播命令，非编译）。
  - **链层（Root）** —— `RunCompiledWorkflow(nodeIndex, seed?)` 运行编译后的前向链；`CompileWorkflow(nodeIndex)` 只编译计划。
  - **结果层（Terminal）** —— `GetNodeResult(nodeIndex, seed?)` 由一个节点的祖先锥计算它的取值；`CompileNodeResult(nodeIndex)` 只编译该锥。
  - **运行句柄家族** 在后台启动同一条编译链并立即返回句柄：`StartCompiledWorkflow` / `ContinueCompiledWorkflow` → 轮询 `GetCompiledRunStatus` → `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`。
- `WorkflowStateTracker` 保存树的 JSON 快照并报告新增/移除/修改的节点与链接，让 agent 以最小上下文观察变化。
- 四个子系统各用一次 `With*` 调用挂载，并在每轮贡献自己的工具与提示文本：**MCP**（`McpScope` / `McpAgentToolkit`）、**技能**（`SkillScope` / `SkillAgentToolkit`）、**子代理**（`SubAgentScope` / `SubAgentAgentToolkit`），以及**管线/对话记录**可观测链（`AgentPipeline`、`AgentTranscript`、`AgentDashboardViewModel`）。
- `VeloxDev.AI` 中的反射工具（`AgentContextAttribute`、`AgentLanguages`、`AgentContextReader`、`AgentCommandDiscoverer`、`AgentMethodInvoker`、`AgentPropertyAccessor`、`AgentTypeResolver`、事件参数类型、`SlotSelectorsAttribute`）支撑类型注册表与工具。

## 快速开始 —— 子页面

本特性的快速开始拆分为以下页面（逐步构建到最后一页的可运行程序）：

| 步骤 | 页面 | 内容 |
|---|---|---|
| 00 | [前置条件](00_前置条件/index.md) | 支持的目标、SDK/运行时、包、你必须提供的服务（树、`IChatClient`、可选 MCP 运行时） |
| 01 | [安装依赖](01_安装依赖/index.md) | 添加 `VeloxDev.Core.Extension` 与其传递 AI 包 |
| 02 | [构建作用域](02_构建作用域/index.md) | `AsAgentScope()` 流式表面：语言、自动发现、提示提供器、工具获取 |
| 03 | [工具预算与宿主策略](03_工具预算与宿主策略/index.md) | 交互安全 0–3、三档调用预算与 `ResetToolCallLimit`、节点执行/通用命令闸门、工具开关、工具审批、UI 线程与脏标记 |
| 04 | [自定义工具与 MCP](04_自定义工具与MCP/index.md) | `WithTools` / `WithQueryTools`、`WithMcps`、MCP 管理工具、自助级别 |
| 05 | [运行一轮对话](05_运行一轮对话/index.md) | 把上下文提供器接到 chat client、会话、管线与对话记录、回复 |
| 06 | [三种执行模型](06_三种执行模型/index.md) | 节点层、Root 链、Terminal 结果工具；只编译的计划 |
| 07 | [终结点结果语义](07_终结点结果语义/index.md) | `GetNodeResult` / `CompileNodeResult`：祖先锥、真实路由、`targetReached` 契约与恢复 |
| 08 | [编译运行句柄](08_编译运行句柄/index.md) | `StartCompiledWorkflow` → `GetCompiledRunStatus` → `Pause`/`Resume`/`Stop`；句柄退休；`RunsOnOurGate` 守卫 |
| 09 | [子代理](09_子代理/index.md) | `SubAgentScope.ForClient` + `WithSubAgents`、五个管理工具、能力收窄、一锅账本、树面板 |
| 10 | [技能与管线](10_技能与管线/index.md) | `WithSkills`、内嵌 vs 文件技能、四个技能工具；`AgentPipeline`、`AgentTranscript`、`WithTranscript` |
| 11 | [仪表盘与状态](11_仪表盘与状态/index.md) | `AgentDashboardViewModel` 以及 MCP / 技能 / 子代理的状态视图模型 |
| 12 | [验证与完整代码](12_验证与完整代码/index.md) | 由 demo 与测试覆盖的清单、单文件可运行程序、运行声明 |

## 代码位于何处

- 根目录：`Src/Core/VeloxDev.Core.Extension/Agent/`（树：`Workflow/`、`MCP/`、`Skills/`、`SubAgents/`、`Pipelines/`、`Dashboard/`）。
- 反射/特性：`Src/Core/VeloxDev.Core/AI/`。
- 工具包：`Agent/Workflow/Functions/WorkflowAgentToolkit.cs`；类别在 `WorkflowToolCategory.cs`。
- Demo（首要证据）：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` 及其旁的对话框。
- 测试：`Src/Core/VeloxDev.Core.Extension.Test/Agent/**` 与 `Src/Core/VeloxDev.Core.Test/AI/*`。
