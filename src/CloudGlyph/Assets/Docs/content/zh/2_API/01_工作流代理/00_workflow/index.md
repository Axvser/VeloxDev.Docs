# 工作流代理 — 命名空间：`VeloxDev.AI.Workflow`

Agent 作用域核心类型。宿主在一块活跃的 `IWorkflowTreeViewModel` 上构造 `WorkflowAgentScope`、以流式方式配置，并把产出的工具/上下文交给 AI 聊天客户端。以下类型均位于 `VeloxDev.AI.Workflow`，实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/`（scope/tracker）与 `Agent/Workflow/AgentContextCollector.cs`。

**证据：** **测试**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*`）+ **Demo**（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`）。

> 入口点是 `AgentEx.AsAgentScope(this IWorkflowTreeViewModel)` 扩展方法——见 [04_agentex](../04_agentex/index.md)。

## WorkflowAgentScope

`public class WorkflowAgentScope(IWorkflowTreeViewModel tree) : IAgentToolCallNotifier`。经由 `tree.AsAgentScope()` 获得。绑定一棵树，保存配置状态，暴露上下文提示词与工具产出，并在每次工具调用后触发 `ToolCalled` 通知。未密封——可直接使用或作为基类。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel { get; }` | 被作用域绑定、所有工具操作的那棵树。 |
| `MaxToolCalls` | `int? { get; private set; }` | 累计工具调用上限；`null` = 不限制。 |
| `AutoMarkDirty` | `bool { get; private set; }` | 为 `true` 时，每次非查询工具调用都会自动把树标脏。 |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | `IAgentToolCallNotifier`——每次工具调用后触发（同时喂给 `WithToolCallCallback`）。 |

**流式配置——以下方法均返回同一作用域以便链式调用。** 典型链（Demo `AgentHelper.ProvideAgent`，第 155–206 行）：

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithOutputLanguage(AgentLanguages.Chinese)
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAutoMarkDirty(false)
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithToolCallCallback(args => { helper.ToolCalled?.Invoke(); return Task.CompletedTask; })
    .WithSelectionHandler(args => helper.SelectionHandler is not null ? helper.SelectionHandler(args) : Task.CompletedTask)
    .WithConfirmationHandler(args => helper.ConfirmationHandler is not null ? helper.ConfirmationHandler(args) : Task.CompletedTask);
scope.WithInteractionSafety(helper.InteractionSafety);
scope.WithTools(
    "Manage MCP servers: ListMcpServers, LoadMcpServers, UnloadMcpServer, DescribeMcpServer.",
    [.. new McpAgentToolkit(helper.Mcp, helper.McpServers).CreateTools()]);
var contextPrompt = scope.ProvideProgressiveContextPrompt();
helper.SetBaseTools(scope.ProvideTools());
```

### 语言与预算

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | 全局默认语言，当单次调用的 `language` 参数为 `null` 时用于提示词/`[AgentContext]` 文档。应在链首调用。 |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` | 要求 LLM 的所有回复使用的语言（与提示词语言相互独立）。会注入 “Output Language” 指令。 |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` | 累计工具调用上限。 |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` | 只读（query）工具调用的独立上限。 |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` | 变更（非 query）工具调用的独立上限。 |

### 类型注册与自动发现

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithEnums` | `WithEnums(Type[] enums, AgentLanguages? language = null)` | 注册枚举类型以进入客户上下文。 |
| `WithInterfaces` | `WithInterfaces(Type[] interfaces, AgentLanguages? language = null)` | 注册接口类型。 |
| `WithComponents` | `WithComponents(Type[] components, AgentLanguages? language = null)` | 注册具体工作流组件类。 |
| `WithData` | `WithData(Type[] dataTypes, AgentLanguages? language = null)` | 注册值对象/数据类型（以纯数据呈现，而非可交互组件）。 |
| `WithAutoDiscovery` | `WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)` | 两遍式程序集扫描（见下）。 |
| `WithAutoDiscovery` | `WithAutoDiscovery(string assemblyName, AgentLanguages? language = null)` | 以简单程序集名调用；若当前 `AppDomain` 未加载该程序集则抛 `ArgumentException`。 |

**`WithAutoDiscovery` 两遍扫描。** 第一遍注册具体工作流组件（实现 `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` 的类）、带 `[AgentContext]` 的枚举与数据类/结构体。第二遍深度扫描每个已注册组件的公开属性 + 非公开字段（后备字段）+ 方法，按语言推断：`[SlotSelectors]` 与成员类型引用的枚举、作为成员类型的接口、`[AgentCommandParameter]` 参数类型，以及非原始类型的值对象结构体。已注册类型与框架内置类型（命名空间 `System*`、`Microsoft*`、`VeloxDev.WorkflowSystem`、`VeloxDev.MVVM`、`VeloxDev.Core.WorkflowSystem`，以及 `FrameworkEnums`/`FrameworkInterfaces`/`FrameworkComponents`/`FrameworkData`）绝不重复加入。`assembly` 为 null 时抛 `ArgumentNullException`。

### 自定义工具与 UI 封送

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` | 注册可变能力的自定义工具（始终包含在 `ProvideTools` 结果中）。可选的 `promptContext` 文本作为 “Custom Tools” 小节注入。 |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` | 注册只读自定义工具——即使开启 `WithAutoMarkDirty(true)` 也绝不自动标脏。 |
| `WithAutoMarkDirty` | `WithAutoMarkDirty(bool enabled = false)` | `true` = 每次变更工具调用后由框架标脏。默认 `false`（提示词指导 Agent 在任务结束时调用一次 `MarkDirty`）。 |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 把每次工具调用封送到给定上下文（如 `SynchronizationContext.Current`）。工作流组件与 UI 绑定，变更必须运行在持有绑定的线程上。 |
| `WithToolCallCallback` | `WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | 每次工具调用后调用的异步处理器；会替换先前注册的处理器。 |

注意：`WithTools`/`WithQueryTools` 的 `AIFunction` 工具会被同一套跟踪包装器包裹（UI 封送、调用计数、回调、自动标脏）；非 `AIFunction` 工具（如原始 MCP 客户端工具）原样加入。

### 能力闸门——代码强制执行，而非仅靠提示词

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithAllowNodeExecution` | `WithAllowNodeExecution(bool enabled = false)` | 运行任意节点业务代码的 Execution 工具的可选闸门：`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow`、`GetNodeResult`。默认拒绝。 |
| `WithAllowedGenericCommands` | `WithAllowedGenericCommands(params string[] commandNames)` | 为 `ExecuteCommandOnNode` / `ExecuteCommandById` 白名单化命令名；`"Command"` 后缀可省略。从未调用 → 泛型命令执行完全禁用（安全默认）。 |

### 交互安全与处理器

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithInteractionSafety` | `WithInteractionSafety(int level)` | 0 静默、1 谨慎（默认）、2 均衡、3 严格；超出 0–3 的值会被钳制。 |
| `WithInteractionSafetyPrompt` | `WithInteractionSafetyPrompt(int level, string promptBody)` | 为某挡（1–3）替换 “Interaction Safety Policy” 正文；第 0 挡始终使用内置静默规则、不可覆盖。 |
| `WithSelectionHandler` | `WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` | 注册 `RequestSelection` 处理器；传 `null` 则移除该工具。处理器必须设置 `SelectedOption`（单选）/ `SelectedOptions`（多选）和/或 `FreeTextResponse`。 |
| `WithConfirmationHandler` | `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` | 注册 `RequestConfirmation` 处理器；传 `null` 则移除该工具。处理器必须设置 `Result`。 |

**语义。** 第 0 挡不注册任何交互工具、也不发出任何策略。第 1–3 挡发出由内嵌 `Safety/Shared.md` + `Safety/Level{n}.md` 拼装、并可附加宿主覆盖文本的 “Interaction Safety Policy”。`AllowAlways` 批准按 `operationKey` 在会话内记忆（`ResolveConfirmationAsync`）。

### 上下文提示词

| 成员 | 签名 | 作用 |
|---|---|---|
| `ProvideAllContexts` | `string ProvideAllContexts()` / `ProvideAllContexts(AgentLanguages)` | 全量上下文：内置参考、框架上下文、框架数据类型、客户上下文、客户数据类型、失败处理协议、自定义工具、交互安全策略、技能、输出语言指令。 |
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `ProvideProgressiveContextPrompt(AgentLanguages)` | 精简的分层式系统提示词（见下）。 |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | 内置枚举（`SlotChannel`、`SlotState`、`RouterCompileMode`）、接口与组件的上下文块。 |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | 已注册客户枚举/接口/组件的上下文块。 |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | `Anchor`、`Offset`、`Size`、`IAccessContext`、`ITaskContext`、`TaskContext`、`ICompileContext`、`IRuntimeContext` 的数据类型上下文。 |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | 已注册客户数据类型的数据类型上下文。 |

**`ProvideProgressiveContextPrompt`** 保持初始提示词精简：关键行为约束、失败处理协议、内置参考、带一行摘要的已注册类型列表、自定义工具、交互安全策略、技能与输出语言指令。完整属性/命令表**故意不预载**——提示词要求 Agent 在对某类型操作前先以完整类型名调用 `GetComponentContext`。

### 工具产出

| 成员 | 签名 | 作用 |
|---|---|---|
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | 在该作用域上构造一个 `WorkflowAgentToolkit`（每个实例各自持有一个 `WorkflowStateTracker`）。 |
| `ProvideTools` | `IList<AITool> ProvideTools()` | `CreateToolkit().CreateTools()`——全部工具。 |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | 仅返回给定类别标志下的工具；经 `WithTools`/`WithQueryTools` 注册的自定义工具始终包含。 |

### `WorkflowAgentScope.SelectionResult`（内嵌）

`public sealed class SelectionResult`——被 `WorkflowAgentToolkit.RequestSelection` 消费的低层结果对象。

| 成员 | 类型 | 说明 |
|---|---|---|
| `SelectedOption` | `string?` | 单选：被选中的选项；取消时为 `null`。 |
| `SelectedOptions` | `IReadOnlyList<string>` | 多选：选中的选项集（无选中则为空）。 |
| `FreeTextResponse` | `string?` | 自由文本回答；未提供则为 `null`/空。 |
| `Single(string? option)` | static | 构造单选结果。 |
| `Multi(IReadOnlyList<string> options, string? freeText = null)` | static | 构造多选结果。 |
| `FreeText(string text)` | static | 构造仅自由文本的结果。 |

## WorkflowStateTracker

`public sealed class WorkflowStateTracker(IWorkflowTreeViewModel tree)`。备忘录式 JSON 快照/差异辅助器，让 Agent 以最小上下文跟踪变化。由工具包自动构造；也可独立使用。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Version` | `long { get; }` | 单调递增的快照版本号。 |
| `TakeSnapshot` | `string TakeSnapshot()` | 构造状态快照（缩进 JSON：`nodeCount`、`linkCount`、`nodes[]` 含 `index`/`id`/`type`/几何/标量属性/`slotIds`、`links[]`），存为上一次快照并使 `Version` +1。 |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | 无上一快照 → `status = "full"` 返回全量状态。否则返回 `status = "diff"`，含按 `RuntimeId` 键控的 `addedNodes`/`removedNodes`/`modifiedNodes`（属性级 `from`/`to`）、`addedLinks`/`removedLinks`，外加前后节点/连接计数。 |

当某组件未实现 `IWorkflowIdentifiable`（无稳定 `RuntimeId`）时抛 `InvalidOperationException`。属性差异只比较标量（`string`/`int`/`double`/`bool`/`long`/`float`/`decimal`）与枚举类型属性。

## AgentContextCollector

`public static class AgentContextCollector`。生成嵌入提示词的人类可读上下文块。`GetAgentContext` 委托给 Core 的 `AgentContextReader`；上述 `Get*Context` 方法渲染 markdown 块，供框架/客户上下文提供方使用。

| 成员 | 签名 | 说明 |
|---|---|---|
| `GetAgentContext` | `string[] GetAgentContext(Type, AgentLanguages)` | 某类型 + 语言的 `[AgentContext]` 值。 |
| `GetAgentContext` | `string[] GetAgentContext(MemberInfo, AgentLanguages)` | 某成员（字段/属性/方法）+ 语言的 `[AgentContext]` 值。 |
| `GetEnumContext` | `string GetEnumContext(Type, AgentLanguages)` | 枚举块：底层类型 + 成员取值表。 |
| `GetInterfaceContext` | `string GetInterfaceContext(Type, AgentLanguages)` | 接口块：基接口、非命令属性、`ICommand` 属性。若 `type` 非接口则抛 `ArgumentException`。 |
| `GetClassContext` | `string GetClassContext(Type, AgentLanguages)` | 类块：接口、开发者指令、`[VeloxProperty]`/槽枚举属性（含 `[SlotSelectors]` 允许类型）、`[VeloxCommand]` 命令。 |
| `GetDataContext` | `string GetDataContext(Type, AgentLanguages)` | 值对象的数据类型块：仅带注解的字段与公开属性（不含命令/槽）。 |
