# 工作流代理 —— 命名空间：`VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit` 把一个作用域内的树变成 MAF 的 `AITool`（完整操作控制），按 `WorkflowToolCategory` 分组；辅助类 `CommandInvoker`、`ComponentPatcher`、`TypeIntrospector` 支撑命令/补丁/schema 工具。所有 JSON 输出都是 `Formatting.None`（紧凑）以省 token；多数工具返回带 `status: "ok" | "error" | "rejected"` 的对象。

实现于 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/`。**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*` —— 工具经公开的 `scope.ProvideTools()` 注册路径调用）+ **Demo**（`AgentHelper.ProvideAgent`）。

## WorkflowAgentToolkit

`public sealed class WorkflowAgentToolkit`。两种构造：`WorkflowAgentToolkit(WorkflowAgentScope scope)` 用于拥有会话额度的作用域，以及一个接受 `outerLedger` 的 `internal` 重载，用于额度是他人份额的作用域。每个工具包拥有一个作用于该树的 `WorkflowStateTracker` 与一个 `ToolCallLedger`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | 可切换表面：`categories` 的内置工具，减去被关闭的，加上自定义工具。 |
| `CreateAllTools`（internal） | `IList<AITool> CreateAllTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | 工具包能提供的全部工具 —— **不**按逐工具开关过滤。宿主 UI 枚举它。 |
| `WrapTool`（internal） | `AITool WrapTool(AITool tool)` | 用 `TrackedAIFunction` 包装 `AIFunction`；其他工具按原样返回。 |
| `CreateAccountingStage`（internal） | `IAgentPipelineStage CreateAccountingStage()` | 计入已完成调用、触发回调并标脏的管线阶段。 |
| `Ledger`（internal） | `ToolCallLedger { get; }` | 本作用域在会话调用记账中的位置。 |

`ResetBudgetToolName` 是 `internal const string` `"ResetToolCallLimit"`；`ResetBudgetOperationKey` 是 `"extend-tool-call-budget"`。

## WorkflowToolCategory

`[Flags] public enum WorkflowToolCategory` —— `CreateTools` 的工具分组选择器。

| 标志 | 值 | 包含 |
|---|---|---|
| `Query` | `1 << 0` | 只读检查（**20 个工具**）。 |
| `Mutation` | `1 << 1` | 结构图编辑（**23 个工具**）。 |
| `Execution` | `1 << 2` | 运行节点业务代码 + 编译运行家族（**12 个工具**，受闸控）。 |
| `Command` | `1 << 3` | 通用白名单命令执行（**2 个工具**，受闸控）。 |
| `Graph` | `1 << 4` | 遍历与寻路（**5 个工具**）。 |
| `Layout` | `1 << 5` | **保留 —— 无工具。** 多节点布局逐节点完成。 |
| `Analytics` | `1 << 6` | `GetNodeStatistics`（**1 个工具**）。 |
| `State` | `1 << 7` | 快照与脏标记（**3 个工具**）。 |
| `Composite` | `1 << 8` | **保留 —— 无工具。** 每个操作都是单次组件命令步骤。 |
| `Interaction` | `1 << 9` | `RequestSelection` / `RequestConfirmation` —— 仅在配置了处理器且安全级别 > 0 时注册（**至多 2 个工具**）。 |
| `All` | 以上全部 | 每个类别。 |

**工具数量。** 两个交互处理器都配置时，上述十个类别合计 **68 个内置工具**（20 + 23 + 12 + 2 + 5 + 0 + 1 + 3 + 0 + 2 = 68；`Layout` 与 `Composite` 不贡献；不含 `Interaction` 的 66 个是无条件注册的 —— `Execution` 与 `Command` 的闸门在每个工具体内检查，而不是靠不注册工具来实现）。此外，无论 `categories` 如何，始终提供三样东西：

- `ResetToolCallLimit` —— 预算逃生舱（见「工具预算与宿主策略」页）；
- 经 `WithTools` / `WithQueryTools` 注册的工具；
- 已挂载子系统（MCP / 技能 / 子代理）贡献的每个工具。

**`Layout` 与 `Composite` 刻意保留：** 多节点布局经 `MoveNode` / `SetNodePosition` 逐节点完成，且每个操作都是单次组件命令步骤，因此框架的撤销/重做栈始终是唯一事实源，绝不被绕过或重复提交。

## 跟踪与记账

每个内置工具都经本地 `T(AITool, name)` 辅助创建，包装为 `TrackedAIFunction`。`TrackedAIFunction`（命名空间 `VeloxDev.AI`，`internal sealed`）把调用编组到作用域的 `SynchronizationContext`，经 `ToolPipeline`（拒绝 + 确认）后运行，并把 `AgentToolCallStarted` / `AgentToolCallCompleted` 报告进作用域的 `AgentPipeline`。

预检闸门 `CheckBudget` 在编组块内、函数体之前运行：

1. 经 `IsToolEnabled` 被关闭的工具 → `'{toolName}' is disabled by host policy. …`；
2. `ResetToolCallLimit` 始终通过；
3. 对子作用域，根的上限（`The session's tool-call budget (N) is spent.`）；
4. 本作用域自身的 `MaxToolCalls`；
5. `MaxWriteToolCalls`（非查询）/ `MaxReadToolCalls`（查询）。

拒绝从不触达函数体，也从不计数。`Succeeded` 的调用由 `AccountingStage` → `AccountAsync` 计数，它在 `AutoMarkDirty` 开启且工具非查询时触发回调并标脏。

`QueryToolNames` 是只读分类：20 个 Query 工具、`TakeSnapshot` / `GetChangesSinceSnapshot`、`GetNodeStatistics`、五个 Graph 工具、`RequestSelection` / `RequestConfirmation`、`ResetToolCallLimit`、`CompileWorkflow` / `CompileNodeResult` / `GetCompileStatus` / `GetExecutionLog`，以及 `SkillAgentToolkit.ToolNames` 与 `SubAgentAgentToolkit.ToolNames` 中的每个名字。

## 工具清单

| 页 | 类别 | 工具 |
|---|---|---|
| [00 · 查询与状态工具](00_查询与状态工具/index.md) | Query + State | 20 + 3 |
| [01 · 变更工具](01_变更工具/index.md) | Mutation | 23 |
| [02 · 执行工具](02_执行工具/index.md) | Execution | 12（含运行句柄家族） |
| [03 · 命令、图、分析与交互工具](03_命令图分析与交互工具/index.md) | Command + Graph + Analytics + Interaction | 2 + 5 + 1 + 2 |
| [04 · 辅助类](04_辅助类/index.md) | — | `CommandInvoker`、`ComponentPatcher`、`TypeIntrospector` |
