# 工作流代理 —— 命名空间：`VeloxDev.AI.Workflow`

核心作用域类型：`WorkflowAgentScope`（流式构建器）、`WorkflowStateTracker`（快照/差异）、`WorkflowAgentContextProvider`（每轮渲染）、`AgentContextCollector`（上下文块）。全部位于 `VeloxDev.AI.Workflow`，实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/`。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/**`）+ **Demo**（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`）。

> 入口点是 `AgentEx.AsAgentScope(this IWorkflowTreeViewModel)` —— 见 `agentex` 页。

## WorkflowAgentScope —— 属性

`public class WorkflowAgentScope(IWorkflowTreeViewModel tree) : IAgentToolCallNotifier`。经 `tree.AsAgentScope()` 获取。非 sealed。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel { get; }` | 每个工具作用的树。 |
| `MaxToolCalls` | `int? { get; private set; }` | 累计调用上限；`null` = 无限制。 |
| `AutoMarkDirty` | `bool { get; private set; }` | `true` 时每个非查询调用自动标脏。 |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | `IAgentToolCallNotifier` —— 每次调用后触发。 |
| `PromptLanguage` | `AgentLanguages { get; }` | `WithPromptLanguage` 设置的提示语言。 |
| `Version` | `long { get; }` | 单调配置版本；每次真实变化前进。 |
| `Changed` | `event EventHandler?` | `Version` 前进时触发。 |
| `DisabledToolNames` | `IReadOnlyList<string> { get; }` | 已关闭的工具。 |
| `Skills` | `SkillScope? { get; private set; }` | 已挂载的技能子系统（`WithSkills`）。 |
| `Mcp` | `McpScope? { get; private set; }` | 已挂载的 MCP 子系统（`WithMcps`）。 |
| `SubAgents` | `SubAgentScope? { get; private set; }` | 已挂载的子代理子系统（`WithSubAgents`）。 |
| `Transcript` | `AgentTranscript? { get; }` | 已挂载的对话记录（`WithTranscript`）。 |
| `Pipeline` | `AgentPipeline { get; }` | 组合出的阶段链。 |
| `Todo` | `TodoProvider? { get; private set; }` | 框架 todo 提供器（`WithTodoTracking`）。 |
| `AgentMode` | `AgentModeProvider? { get; private set; }` | 框架模式提供器（`WithAgentModes`）。 |
| `CheckpointStore` | `IExecutionCheckpointStore? { get; private set; }` | 宿主检查点存储（`WithCheckpointStore`）。 |

## WorkflowAgentScope —— 流式表面

所有 `With*` 都返回同一作用域。按用途分组。

### 语言与预算

| 成员 | 签名 |
|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` |

### 类型注册

| 成员 | 签名 |
|---|---|
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `(Type[] …, AgentLanguages? language = null)` |
| `WithAutoDiscovery` | `WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)` |
| `WithAutoDiscovery` | `WithAutoDiscovery(string assemblyName, AgentLanguages? language = null)` |

### 自定义工具

| 成员 | 签名 |
|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` |

### 逐工具开关

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithToolEnabled` | `WithToolEnabled(string toolName, bool enabled = true)` | 流式；仅在真实移动时提升 `Version`。 |
| `SetToolEnabled` | `bool SetToolEnabled(string toolName, bool enabled)` | 运行时；返回开关是否移动。 |
| `IsToolEnabled` | `bool IsToolEnabled(string toolName)` | 读取当前状态。 |

### 能力闸门

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithAllowNodeExecution` | `WithAllowNodeExecution(bool enabled = false)` | 运行代码的执行工具的选择性闸门。 |
| `WithAllowedGenericCommands` | `WithAllowedGenericCommands(params string[] commandNames)` | `ExecuteCommandOnNode` / `ExecuteCommandById` 的白名单。 |
| `WithAutoMarkDirty` | `WithAutoMarkDirty(bool enabled = false)` | 变更后自动标脏。 |

### 交互与审批

| 成员 | 签名 |
|---|---|
| `WithInteractionSafety` | `WithInteractionSafety(int level)` |
| `WithInteractionSafetyPrompt` | `WithInteractionSafetyPrompt(int level, string promptBody)` |
| `WithSelectionHandler` | `WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` |
| `WithConfirmationHandler` | `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` |
| `WithToolApproval` | `WithToolApproval(bool enabled = true)` |

### 宿主与管线

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 编组每次工具调用。 |
| `WithToolCallCallback` | `WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | 每次调用后的异步处理器。 |
| `WithLogWriter` | `WithLogWriter(ILogWriter? writer)` | 路由编译运行的日志行；`LogFilePath` 暴露 `TextWriterLogWriter` 的路径。 |
| `WithCheckpointStore` | `WithCheckpointStore(IExecutionCheckpointStore? store)` | `ContinueCompiledWorkflow` 的读取来源。 |
| `WithSessionConfiguration` | `WithSessionConfiguration(Action<RuntimeContext> configure)` | 应用于每次编译运行的 `RuntimeContext`，早于运行工具填补未设之处。 |
| `WithTranscript` | `WithTranscript(AgentTranscript transcript)` | 挂载对话记录；已挂载时抛 `InvalidOperationException`。 |
| `WithContextProvider` | `WithContextProvider(Func<WorkflowAgentScope, AIContextProvider> factory)` | 添加宿主提供器工厂。 |

### 子系统与框架脚手架

| 成员 | 签名 |
|---|---|
| `WithSkills` | `WithSkills(string rootPath)` / `WithSkills(SkillScope skills)` |
| `WithMcps` | `WithMcps(McpScope mcp)` |
| `WithSubAgents` | `WithSubAgents(SubAgentScope subAgents)` |
| `WithTodoTracking` | `WithTodoTracking(TodoProviderOptions? options = null)` |
| `WithAgentModes` | `WithAgentModes(AgentModeProviderOptions options)` |
| `WithContextCompaction` | `WithContextCompaction(int maxContextWindowTokens, int maxOutputTokens)` |

### 提示、工具与提供器

| 成员 | 签名 | 说明 |
|---|---|---|
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | 精简提示。 |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `(AgentLanguages)` | 完整提示。 |
| `ProvideFrameworkContext` / `ProvideCustomerContext` | `string …(AgentLanguages = English)` | 上下文块。 |
| `ProvideFrameworkDataContext` / `ProvideCustomerDataContext` | `string …(AgentLanguages = English)` | 数据块。 |
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | 每个作用域缓存一个实例。 |
| `ProvideTools` | `IList<AITool> ProvideTools()` / `(WorkflowToolCategory)` | 工具集。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider()` | 单个 `WorkflowAgentContextProvider`。 |
| `CreateContextProviders` | `IReadOnlyList<AIContextProvider> CreateContextProviders()` | 完整定序列表。 |
| `CreateSkillToolkit` | `SkillAgentToolkit CreateSkillToolkit()` | 未挂载技能作用域时抛 `InvalidOperationException`。 |

### 嵌套 `SelectionResult`

`public sealed class SelectionResult` —— `RequestSelection` 工具消费的底层结果：`SelectedOption`（`string?`）、`SelectedOptions`（`IReadOnlyList<string>`）、`FreeTextResponse`（`string?`），外加 `static Single(string?)` / `Multi(IReadOnlyList<string>, string? freeText = null)` / `FreeText(string)`。

## WorkflowStateTracker

`public sealed class WorkflowStateTracker(IWorkflowTreeViewModel tree)` —— 备忘式 JSON 快照/差异，让 agent 以最小上下文跟踪变化。由工具包自动构造，也可独立使用。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Version` | `long { get; }` | 单调递增的快照版本。 |
| `TakeSnapshot` | `string TakeSnapshot()` | 构建快照（缩进 JSON：`nodeCount`、`linkCount`、含 `index`/`id`/`type`/几何/标量属性/`slotIds` 的 `nodes[]`、`links[]`），存为最近快照并递增 `Version`。 |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | 无上一快照 → `status = "full"` 返回全部状态；否则 `status = "diff"`，含按 `RuntimeId` 键控的 `addedNodes`/`removedNodes`/`modifiedNodes`（属性级 `from`/`to`）、`addedLinks`/`removedLinks`，以及前后计数。 |

当组件未实现 `IWorkflowIdentifiable`（无稳定 `RuntimeId`）时抛 `InvalidOperationException`。属性差异只比较标量（`string`/`int`/`double`/`bool`/`long`/`float`/`decimal`）与枚举类型属性。

## WorkflowAgentContextProvider

`public sealed class WorkflowAgentContextProvider : AIContextProvider`。**每轮工具与指令的唯一来源。** 以其缓存的渲染按作用域 `ContextKey`（`Version` 加预算用量档）键控；未变化的一轮不加锁、不分配，返回同一个 `AIContext` 实例。其 `StateKeys` 按作用域（同一作用域两个提供器共享键，两个作用域绝不共享）。

```csharp
public WorkflowAgentContextProvider(WorkflowAgentScope scope)
public override IReadOnlyList<string> StateKeys { get; }
protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext, CancellationToken)
```

## AgentContextCollector

`public static class AgentContextCollector` —— 产出内嵌于提示中的可读上下文块。`GetAgentContext` 委托给 Core 的 `AgentContextReader`；`Get*Context` 方法渲染框架/客户提供器所用的 markdown 块。

| 成员 | 签名 | 说明 |
|---|---|---|
| `GetAgentContext` | `string[] GetAgentContext(Type, AgentLanguages)` / `(MemberInfo, AgentLanguages)` | 类型 / 成员 + 语言的 `[AgentContext]` 取值。 |
| `GetEnumContext` | `string GetEnumContext(Type, AgentLanguages)` | 枚举块：底层类型 + 成员取值表。 |
| `GetInterfaceContext` | `string GetInterfaceContext(Type, AgentLanguages)` | 接口块；`type` 非接口时抛 `ArgumentException`。 |
| `GetClassContext` | `string GetClassContext(Type, AgentLanguages)` | 类块：接口、开发者指令、`[VeloxProperty]`/槽枚举属性（含 `[SlotSelectors]` 允许类型）、`[VeloxCommand]` 命令。 |
| `GetDataContext` | `string GetDataContext(Type, AgentLanguages)` | 值对象的数据块。 |
