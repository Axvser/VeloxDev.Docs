# WorkflowAgentScope

`VeloxDev.AI.Workflow.WorkflowAgentScope` 在一棵工作流树上配置并运行一个智能体。它持有树、工具面、调用会话与上下文 provider 链。每个 `With*` 方法都返回同一个作用域，因此宿主可以把它当作一条链来配置。

属于其他功能的成员记录在对应页面：权限与预算成员见[智能体安全与预算](../../18_智能体安全与预算/index.md)，提示与技能成员见[智能体上下文与技能](../../19_智能体上下文与技能/index.md)，`WithMcps` / `Mcp` 见 [MCP 集成](../../20_MCP集成/index.md)，`WithSubAgents` / `SubAgents` 见[子智能体](../../21_子智能体/index.md)，`WithTranscript` / `Transcript` / `Pipeline` 见[智能体仪表盘与转录](../../22_智能体仪表盘与转录/index.md)。

## 创建

`AsAgentScope()` 是扩展方法 `AgentEx.AsAgentScope(this ITreeComponent)`。

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope();
```

作用域包装这棵树，既不复制也不替换它。

## 属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Tree` | `ITreeComponent` | 此作用域操作的工作流树；由 `LoadWorkflow` 替换。 |
| `Version` | `long` | 作用域所有可配置内容的单调版本号。任何改变智能体所见的设置都会推进它，因此基于它缓存的 provider 只在真正变化时重渲染。 |
| `MaxToolResultChars` | `int` | 单次工具结果的文本上限。超过上限的结果被截断信封替换。默认 64 KiB；`0` 关闭上限。 |
| `MaxTokens` | `int?` | 会话 token 上限，`null` 表示无上限。在包括 `Bypass` 在内的所有模式下强制执行。 |
| `MaxToolCalls` | `int?` | 工具调用总数上限，`null` 表示无上限。在 `Bypass` 下既不计数也不强制。 |
| `InputTokens` / `OutputTokens` / `TotalTokens` | `long` | provider 为此作用域运行上报的花费。 |
| `CheckpointStore` | `IExecutionCheckpointStore?` | 编译运行写入位置的地方。`null` 表示作用域自有的内存存储。 |
| `Todo` | `TodoProvider?` | 在 `WithTodoTracking` 挂载后，Agent Framework 的待办列表。 |
| `AgentMode` | `AgentModeProvider?` | 在 `WithAgentModes` 挂载后，Agent Framework 的运行模式。 |
| `PromptLanguage` | `AgentLanguages` | `WithPromptLanguage` 设置的提示语言。 |

## 事件

| 名称 | 类型 | 说明 |
|---|---|---|
| `Changed` | `EventHandler` | 智能体所见内容变化时触发——`With*` 调用、工具开关、挂载子系统。在触发线程上直接触发，不做线程编组。 |
| `TreeChanged` | `EventHandler` | `LoadWorkflow` 替换作用域树后触发。 |
| `ToolCalled` | `EventHandler<AgentToolCallEventArgs>` | **成功**的工具调用后触发。被拒绝或失败的调用改由 `Pipeline` 上的 `AgentToolCallCompleted` 发布。 |

## 工具注册

| 方法 | 说明 |
|---|---|
| `WorkflowAgentScope WithTools(string? promptContext, params AITool[] tools)` | 注册可变更的自定义工具，并入 `ProvideTools`。每个 `AIFunction` 都会被包装，从而获得 UI 线程编组、记账、调用回调与可选的脏标记。 |
| `WorkflowAgentScope WithQueryTools(string? promptContext, params AITool[] tools)` | 注册只读自定义工具。行为同 `WithTools`，但从不自动标记树为脏。 |
| `IList<AITool> ProvideTools()` | 所有工具的便捷快照。若工具集须跟随后续变化，优先用 `CreateToolkit().CreateTools()`。 |
| `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | 所选分类组的快照。自定义工具始终包含。 |
| `WorkflowAgentToolkit CreateToolkit()` | 作用域唯一的 toolkit，首次使用时创建。它持有调用账本与快照历史，因此所有调用方共享同一实例。 |
| `WorkflowAgentScope WithToolEnabled(string toolName, bool enabled = true)` | 按名称开关一个工具。被关闭的工具从下一轮起不再提供。 |
| `bool SetToolEnabled(string toolName, bool enabled)` | `WithToolEnabled` 的运行时对应物；推进 `Version` 并返回开关是否真的改变。 |
| `bool IsToolEnabled(string toolName)` | 指定工具当前是否被提供。 |
| `IReadOnlyList<string> DisabledToolNames` | 被关闭工具名称的快照。 |

`WithTools` 会保留自定义工具的提示文本，供 provider 注入。非 `AIFunction` 工具会原样加入，不获得任何跟踪；用 SDK 的 `AsAIFunction()` 包装它即可加入。

## 会话接线

| 方法 | 说明 |
|---|---|
| `WorkflowAgentScope WithWorkflowLoader(Func<string, ITreeComponent> loader)` | 提供 `LoadWorkflow` 使用的加载器。`TreeChanged` 触发时宿主应重新绑定自己的表面。 |
| `ITreeComponent LoadWorkflow(string json)` | 用反序列化的图替换树。旧树保持原样，由宿主负责关闭。 |
| `WorkflowAgentScope WithSynchronizationContext(SynchronizationContext? context)` | 把每次工具调用编组到 UI 线程。工作流组件绑定 UI，因此变更必须在绑定线程上执行；初始化时传 `SynchronizationContext.Current`。 |
| `WorkflowAgentScope WithLogWriter(ILogWriter? writer)` | 把编译运行的日志行同时发送到 sink 与内存会话日志。 |
| `WorkflowAgentScope WithCheckpointStore(IExecutionCheckpointStore? store)` | 设置编译运行写入检查点的位置；`null` 恢复内存存储。 |
| `WorkflowAgentScope WithSessionConfiguration(Action<RuntimeContext> configure)` | 配置编译运行使用的 `RuntimeContext`——重试策略、观察者、错误 sink、补偿器、闸门、检查点存储、日志写入器。在作用域自身设置之后、toolkit 的设置之前调用。 |
| `WorkflowAgentScope WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | 注册成功调用的处理器，替换此前注册的处理器。 |
| `bool TryStopRun(IRuntimeContext context)` | 请求由宿主配置的会话所标识的后台编译运行停止。返回 `false` 表示此作用域不持有该运行。 |

任何绑定的 UI 都需要 `WithSynchronizationContext`：否则工具会在聊天客户端调用它的线程上运行。

## Provider 与运行时附加项

| 方法 | 说明 |
|---|---|
| `AIContextProvider CreateContextProvider()` | 创建工作流上下文 provider——每次调用渲染提示文本与完整工具集的对象。 |
| `IReadOnlyList<AIContextProvider> CreateContextProviders()` | 创建所有要挂载的 provider，顺序固定：压缩（若已配置）、工作流 provider、每个已挂载子系统（技能、MCP、子智能体）各一个，最后是 `WithContextProvider` 工厂各一个。把结果传给 `ChatClientAgentOptions.AIContextProviders`。 |
| `WorkflowAgentScope WithContextProvider(Func<WorkflowAgentScope, AIContextProvider> factory)` | 添加一个 provider 工厂。工厂只运行一次，按注册顺序。不要贡献作用域已提供的工具名——框架会做并集且不去重。 |
| `WorkflowAgentScope WithContextCompaction(int maxContextWindowTokens, int maxOutputTokens)` | 约束对话历史：窗口将满时汇总旧工具结果、丢弃旧回合。传入宿主模型的真实上下文窗口与输出上限。 |
| `WorkflowAgentScope WithTodoTracking(TodoProviderOptions? options = null)` | 加入 Agent Framework 的待办工具与每轮未完成事项简报。这些工具不被包装：它们既不碰树，也不消耗调用预算。 |
| `WorkflowAgentScope WithAgentModes(AgentModeProviderOptions options)` | 加入 Agent Framework 的 `mode_set` / `mode_get` 工具。模式集合与起始模式由宿主决定。 |
| `ValueTask DisposeAsync()` | 取消并等待运行中的子智能体，拆掉所有 MCP 连接。可多次调用。 |

`CreateContextProviders` 固定顺序而不按挂载顺序，因为框架会把各 provider 的贡献拼接起来——否则挂载顺序就会决定提示的读法。

## 类：WorkflowAgentContextProvider

`VeloxDev.AI.Workflow.WorkflowAgentContextProvider : AIContextProvider` 在每次调用时渲染作用域当前的技能、提示文本与完整工具集。它是工具的唯一来源：保持 `ChatOptions.Tools` 为空，因为框架会把 provider 工具与该列表做并集且不按名去重。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `WorkflowAgentContextProvider(WorkflowAgentScope scope)` | 把 provider 绑定到作用域；为 null 时抛 `ArgumentNullException`。 |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | 逐作用域键，使各自拥有作用域的两棵树不冲突。 |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | 渲染每轮贡献。 |

渲染结果基于作用域 `Version` 缓存；未变化的回合不分配内存并返回上一次渲染。

## 相关

- [WorkflowAgentToolkit](../01_工作流工具集/index.md) —— `CreateToolkit` 背后的工具目录。
- [智能体安全与预算](../../18_智能体安全与预算/index.md) —— 权限、预算与脏标记。
