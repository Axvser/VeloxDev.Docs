# 工作流代理 — API：子代理

`VeloxDev.AI.SubAgents` 命名空间（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/`）让代理能够**在后台派发子代理**，每个子代理拿到派发者能力的一份收窄切片。公开面由七个类型组成：子系统本身与它的上下文提供器、面向 Agent 的工具包、状态与摘要那一对，以及两个树视图模型。

入口：`SubAgentScope.ForClient(chatClient)` → `workflowScope.WithSubAgents(subAgents)`。此后模型通过五个工具触达本子系统（`SpawnSubAgent`、`WaitSubAgents`、`GetSubAgentResult`、`ListSubAgents`、`CancelSubAgent`）。

**证据：** **测试**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/*` —— 九个 `[TestClass]` 文件，是这些页面每一条论断的主要来源）+ **Demo**（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` 第 306-307 行，以及 `Examples/Workflow/Avalonia/Demo/Views/Workflow/` 下的子代理树面板）。凡无测试直接覆盖、仅由源码推断的行为均标注 *推断所得*。

## API — 栏目

- [subagentscope](00_子代理作用域/index.md) —— `SubAgentScope`：构造、spawn 额度（`SpawnBudget`、`WithSpawnBudget`）、深度（`MaxDepth`、`WithSubAgentDepth`）、名册（`Children`、`Snapshot`、`Version`、`Changed`）、销毁。
- [toolkit-and-provider](01_工具包与上下文提供器/index.md) —— `SubAgentAgentToolkit`（五个 `AITool`、`ToolNames`、三个 `CreateTools` 重载）与 `SubAgentAgentContextProvider`（每轮的提示词与工具、`StateKeys`）。
- [state-and-rows](02_状态与行/index.md) —— `SubAgentState`、不可变的 `SubAgentSummary`（跨线程快照）与可绑定的 `SubAgentStatusViewModel` 行。
- [tree](03_树视图模型/index.md) —— `SubAgentTreeNodeViewModel` 与 `SubAgentTreeViewModel`：把按作用域分开的名册投影成一棵树，含时长、token 与子树合计。

## `WorkflowAgentScope` 上的集成成员

本子系统从工作流特性自己的作用域（`VeloxDev.AI.Workflow`）接入，与子代理相关的成员如下：

| 成员 | 签名 | 备注 |
|---|---|---|
| `SubAgents` | `SubAgentScope? { get; }` | 在 `WithSubAgents` 挂上之前为 `null`。 |
| `WithSubAgents` | `WorkflowAgentScope WithSubAgents(SubAgentScope)` | 挂上子系统，调用 `SubAgentScope.Attach(this)`，转交 UI `SynchronizationContext`，并把该子系统的提供器与本作用域的 `ToolPipeline` 组合后注册。`null` 抛 `ArgumentNullException`。 |
| `AllowNodeExecution` | `bool { get; }` —— **internal** | spawn 用它判断节点执行能否往下交。internal，测试经 `InternalsVisibleTo` 触达。 |
| `MaxReadToolCalls` / `MaxWriteToolCalls` | `int? { get; }` —— **internal** | spawn 用来夹取读/写档位；请求沉默时由子代理继承。 |
| `GrantInteractionTo` | `void GrantInteractionTo(WorkflowAgentScope child)` —— **internal** | 把交互安全等级、各等级的提示词覆盖表、以及两个处理器一起复制到子作用域上。 |
| `GrantCustomToolsTo` | `void GrantCustomToolsTo(WorkflowAgentScope child, IReadOnlyCollection<string> granted)` —— **internal** | 按授予结果重新注册本作用域自定义工具**分组**的子集，连用法说明一起。 |
| `ParentLedger` | `ToolCallLedger? { get; set; }` —— **internal** | 子作用域链上去的外层账本，让它的调用记在根上。由 `CreateToolkit()` 读取。 |

spawn 用来做收窄的三个能力源，就是父作用域自己的子系统：`Skills`（`SkillScope`，经其 internal 的 `GrantableNames` / `CreateNarrowed` 收窄）、`Mcp`（`McpScope`，经其 internal 的 `GrantableNames` / `CreateGrantedView` 收窄），以及工具开关 `IsToolEnabled` / `WithToolEnabled` / `SetToolEnabled` / `DisabledToolNames`。

> 源码：`WorkflowAgentScope.cs` 第 251-296 行（授予辅助）、1385-1397 行（账本 + 工具包）、1452 行（`SubAgents`）、1659-1673 行（`WithSubAgents` 主体）；`SkillScope.cs` 第 353-378 行（`GrantableNames` / `CreateNarrowed`）；`McpScope.cs` 第 429-500 行（`GrantableNames` / `CreateGrantedView`）。
