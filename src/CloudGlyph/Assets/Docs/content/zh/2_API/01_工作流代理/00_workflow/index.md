# Workflow Agent — 命名空间：`VeloxDev.AI.Workflow`

### `WorkflowAgentScope`

通过 `tree.AsAgentScope()` 获得的流式构建器。实现 `IAgentToolCallNotifier`。持有作用域内的树（`Tree`）、`MaxToolCalls`、`AutoMarkDirty` 与 `ToolCalled` 事件。

#### `AsAgentScope`（入口）

**签名：** `public static WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` —— 见 `AgentEx`。
**返回：** 绑定到 `tree` 的新 `WorkflowAgentScope`。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 155 行。
**说明：** 这是唯一入口；没有树就无法使用作用域。

#### 流式配置 —— 完整表面

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithPromptLanguage` | `WorkflowAgentScope WithPromptLanguage(AgentLanguages)` | 提示词/文档的默认语言；应放在链首。 |
| `WithOutputLanguage` | `WorkflowAgentScope WithOutputLanguage(AgentLanguages)` | LLM 回复必须使用的语言（与提示词语言相互独立）。 |
| `WithMaxToolCalls` | `WorkflowAgentScope WithMaxToolCalls(int)` | 累计工具调用上限。 |
| `WithMaxReadToolCalls` | `WorkflowAgentScope WithMaxReadToolCalls(int)` | 只读（查询）工具调用独立上限。 |
| `WithMaxWriteToolCalls` | `WorkflowAgentScope WithMaxWriteToolCalls(int)` | 变更工具调用独立上限。 |
| `WithAutoMarkDirty` | `WorkflowAgentScope WithAutoMarkDirty(bool enabled = false)` | 每个非查询工具调用后自动 `MarkDirty`。默认 `false`（此时提示词会指示 Agent 调用一次 `MarkDirty`）。 |
| `WithAllowNodeExecution` | `WorkflowAgentScope WithAllowNodeExecution(bool enabled = false)` | `ExecuteNode`/`ExecuteNodes`/`BroadcastNode`/`ReverseBroadcastNode`/`RunCompiledWorkflow` 的选择加入门禁。默认拒绝。 |
| `WithAllowedGenericCommands` | `WorkflowAgentScope WithAllowedGenericCommands(params string[])` | 为 `ExecuteCommandOnNode`/`ExecuteCommandById` 白名单命令名；`"Command"` 后缀可省。从不调用 → 通用命令执行关闭。 |
| `WithSynchronizationContext` | `WorkflowAgentScope WithSynchronizationContext(SynchronizationContext?)` | 把每次工具调用 marshal 到 UI 线程。设置时传 `SynchronizationContext.Current`。 |
| `WithToolCallCallback` | `WorkflowAgentScope WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` | 每次工具调用后的异步回调。替换之前注册的任何处理器。 |
| `WithSelectionHandler` | `WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` | 注册 `RequestSelection` 处理器；`null` 移除该工具。 |
| `WithConfirmationHandler` | `WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` | 注册 `RequestConfirmation` 处理器；`null` 移除该工具。 |
| `WithInteractionSafety` | `WorkflowAgentScope WithInteractionSafety(int level)` | 0 静默、1 谨慎、2 平衡、3 严格；钳制在 0-3。 |
| `WithInteractionSafetyPrompt` | `WorkflowAgentScope WithInteractionSafetyPrompt(int level, string promptBody)` | 覆盖某挡（1-3）的提示词正文；第 0 挡不可覆盖。 |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(Assembly, AgentLanguages? = null)` | 扫描程序集并注册组件/枚举/接口/数据（两轮，去重）。 |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(string assemblyName, AgentLanguages? = null)` | 按简单程序集名同上；当前 `AppDomain` 找不到时抛 `ArgumentException`。 |
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `WorkflowAgentScope With*(Type[], AgentLanguages? = null)` | 按语言桶手动注册类型。 |
| `WithTools` | `WorkflowAgentScope WithTools(string? promptContext, params AITool[])` | 合并可变更的自定义工具 + 可选提示词文本。 |
| `WithQueryTools` | `WorkflowAgentScope WithQueryTools(string? promptContext, params AITool[])` | 合并只读自定义工具（永不自动置脏）。 |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `string ProvideAllContexts(AgentLanguages)` | 完整上下文字符串（框架 + 客户上下文、失败协议、安全策略、技能）。 |
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | 精简的渐进式系统提示词。 |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | 内置框架枚举/接口/组件的上下文。 |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | 已注册客户枚举/接口/组件的上下文。 |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | 框架值类型的数据上下文（`Anchor`、`Offset`、`Size`、`IAccessContext`、`ITaskContext`、`TaskContext`、`ICompileContext`、`IRuntimeContext`）。 |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | 已注册客户数据类型的数据上下文。 |
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | 基于此作用域构建 `WorkflowAgentToolkit`。 |
| `ProvideTools` | `IList<AITool> ProvideTools()` | `CreateToolkit().CreateTools()` —— 全部工具。 |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory)` | 仅给定分类旗标下的工具；自定义工具始终包含。 |

#### `WorkflowAgentScope.WithAutoDiscovery`（两轮扫描）

**签名：** `public WorkflowAgentScope WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)`
**返回：** 同一个作用域，便于链式调用。
**异常：** `assembly` 为 null 时抛 `ArgumentNullException`；字符串重载在程序集未加载时抛 `ArgumentException`。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 159-160 行。
**说明：** 第一轮注册具体工作流组件、带 `[AgentContext]` 的枚举与数据类型；第二轮深度扫描每个已注册组件的属性/字段/方法，推断枚举（经 `[SlotSelectors]`）、接口、`[AgentCommandParameter]` 参数类型以及非基元值对象。已注册类型与框架内置类型绝不重复加入。*复杂度见 SE 复杂度分析页。*

#### `WorkflowAgentScope.ProvideProgressiveContextPrompt`

**签名：** `public string ProvideProgressiveContextPrompt()` / `public string ProvideProgressiveContextPrompt(AgentLanguages language)`
**返回：** 精简系统提示词：关键行为约束、失败处理协议、内置参考、带一行摘要的已注册类型列表、自定义工具分区、交互安全策略、技能与输出语言指令。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 200 行。
**说明：** 渐进式披露 —— 刻意不预载完整属性/命令表；提示词指示 Agent 在操作某类型前先调用 `GetComponentContext`。

#### `WorkflowAgentScope.WithSelectionHandler` / `WithConfirmationHandler`

**签名：** `public WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` 与 `public WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)`
**返回：** 同一个作用域。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 170-179 行；宿主对话框在 `Examples/Workflow/WinForms/Demo/Form1.cs`（`ShowSelectionDialogAsync`、`ShowConfirmationDialogAsync`）。
**说明：** 处理器为 null → 对应工具不注册。选择处理器须设置 `SelectedOption`/`SelectedOptions`/`FreeTextResponse`；确认处理器须设置 `Result`。`AllowAlways` 审批会按 `operationKey` 在会话内记住。

#### `WorkflowAgentScope.WithInteractionSafety`

**签名：** `public WorkflowAgentScope WithInteractionSafety(int level)`
**返回：** 同一个作用域。
**异常：** 无（0-3 之外的值被钳制）。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 182 行。
**说明：** 第 0 挡不注册交互工具、不生成安全策略；1-3 挡生成"Interaction Safety Policy"，由内嵌 `Safety/Shared.md` + `Safety/Level{n}.md` 及 `WithInteractionSafetyPrompt` 覆盖构成。

#### `WorkflowAgentScope.CreateToolkit` / `ProvideTools`

**签名：** `public WorkflowAgentToolkit CreateToolkit()` 与 `public IList<AITool> ProvideTools()` / `public IList<AITool> ProvideTools(WorkflowToolCategory categories)`
**返回：** 工具包 / `AITool` 列表。
**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 197-204 行。
**说明：** 每个内置工具都包装在 `TrackedAIFunction` 中（UI 线程 marshal、调用计数、最大调用强制、`ToolCalled` 回调、可选自动置脏）。经 `WithTools`/`WithQueryTools` 注册的自定义 `AIFunction` 同样包装；非 `AIFunction` 工具（原始 MCP 工具）原样加入。

### `WorkflowStateTracker`

备忘录式 JSON 快照/差异辅助类。由工具包构造（`new WorkflowStateTracker(scope.Tree)`）；也可独立使用。

#### `TakeSnapshot`

**签名：** `public string TakeSnapshot()`
**返回：** 当前树状态的缩进 JSON 字符串（`nodeCount`、`linkCount`、`nodes[]` 含 index/id/type/几何/标量属性/slotIds、`links[]`），并把它存为最近一次快照。
**异常：** 组件未实现 `IWorkflowIdentifiable`（无稳定 `RuntimeId`）时抛 `InvalidOperationException`。
**示例：** `WorkflowAgentToolkit.cs` 中的工具 `TakeSnapshot`。
**说明：** 每次快照 `Version` 自增。

#### `GetChangesSinceLastSnapshot`

**签名：** `public string GetChangesSinceLastSnapshot()`
**返回：** 若无先前快照，返回 `status = "full"` 的整个状态对象；否则返回 `status = "diff"` 对象，含按 `RuntimeId` 键控的 `addedNodes`/`removedNodes`/`modifiedNodes`（属性级 `from`/`to`）与 `addedLinks`/`removedLinks`，以及 `previous/current` 节点、连接计数。
**示例：** `WorkflowAgentToolkit.cs` 中的工具 `GetChangesSinceSnapshot`。
**说明：** 属性差异只比较标量与枚举类型属性（string/int/double/bool/long/float/decimal/enum）。
