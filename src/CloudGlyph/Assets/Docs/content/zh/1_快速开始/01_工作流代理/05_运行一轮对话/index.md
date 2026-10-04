# 05 · 运行一轮对话

这一页才真正涉及模型。此前的全部内容都是离线配置。

## 1. 构建 agent

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI.Pipelines;

scope.WithTranscript(transcript);                                 // 先挂载对话记录

var instructions = scope.ProvideProgressiveContextPrompt();       // 静态骨架

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = instructions },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);                                  // 同时观察 Run 与 RunStreaming

var session = await agent.CreateSessionAsync();
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

这里两条规则是承重的：

- **上下文提供器是工具的唯一来源。** Agent Framework 会把提供器贡献的工具与 `ChatOptions.Tools` 携带的工具做并集，而该并集**不**按名去重。同一工具经两条通道供给会把同一份发给模型两次。因此让 `ChatOptions.Tools` 保持为空 —— 提供器才是渲染工具列表的地方。
- **在 agent 存在之前挂载对话记录。** 作用域在那一刻从对话记录组合出它的管线阶段链；agent 随后被这条链包装。

便捷重载 `AgentClientExtensions.AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` 做的是同一件事，只是不必写出 `ChatClientAgentOptions`。

**预期结果：** `agent` 是一个 `AIAgent`，`session` 创建成功；当 `chatClient` 是真实模型客户端时，此时尚无任何网络调用。

## 2. 提供器逐轮渲染

`WorkflowAgentContextProvider`（`scope.CreateContextProviders()` 之一）正是让挂载、关闭或加载某样东西在**下一轮**生效、而无需重建 agent 的机制。它把缓存的渲染按 `scope.ContextKey`（作用域 `Version` 加上预算用量档）键控：

- 在**未变化**的一轮里，它不加锁、不分配 —— 返回上一次返回的**同一个** `AIContext` 实例。
- 在变化的一轮里，它重建指令（`BuildDynamicInstructions`），并在作用域 `Version` 移动时重建工具列表（`BuildDynamicTools`）。

`CreateContextProviders()` 以一个**固定**顺序装配（这样 `With*` 调用的先后不会改变提示的读法）：

1. 压缩提供器（若调用了 `WithContextCompaction`）；
2. 本作用域自身的 `WorkflowAgentContextProvider`；
3. 技能提供器（若有 `WithSkills`）；
4. MCP 提供器（若有 `WithMcps`）；
5. 子代理名册提供器（若有 `WithSubAgents`）；
6. 框架的 todo 提供器（若有 `WithTodoTracking`）与模式提供器（若有 `WithAgentModes`）；
7. 每个经 `WithContextProvider` 注册的工厂各一个。

**预期结果：** 配置未变时连续调用提供器两次返回同一个 `AIContext` 实例；两次之间调用 `SetToolEnabled(...)` 会让第二次渲染出新实例。

## 3. 可选的框架脚手架

```csharp
scope.WithTodoTracking()                     // 框架的 todos_* 工具 + 未完成工作提示
     .WithAgentModes(new AgentModeProviderOptions { /* Modes = [...], DefaultMode = "build" */ })
     .WithContextCompaction(maxContextWindowTokens: 128_000, maxOutputTokens: 8_192);
```

- `WithTodoTracking(options?)` 启用框架的 todo 列表；`todos_*` 工具来自框架自带的提供器，**刻意不**像 workflow 工具那样被包装（它们既不读也不写树）。
- `WithAgentModes(options)` 增加 `mode_set` / `mode_get` 工具。`options` 必填 —— 没有有用的默认集。属性 `AgentMode` 让宿主切换模式。
- `WithContextCompaction(maxContextWindowTokens, maxOutputTokens)` 限定对话长度：超过某阈值后最旧的工具结果被摘要，超过下一阈值后最旧的轮次被丢弃。**这两个数字是关于宿主模型的事实** —— 传真实的上下文窗口与输出上限，别猜（demo 正因此省略了这次调用）。

**预期结果：** `WithTodoTracking` 后向模型提供框架的 `todos_*` 工具；这些调用不消耗 workflow 预算，也不把树标记为脏。

## 4. 发送一轮

```csharp
AgentResponse response = await agent.RunAsync("列出现有节点，然后添加一个 Demo.ViewModels.NetworkRequest 类型的节点。", session);
Console.WriteLine(response.Text);
```

**预期结果：** 模型作答，若它决定行动，对话记录会按序新增 `ToolCall` 条目；每次工具调用在 UI 线程上运行（若注册了 `SynchronizationContext`），计入预算，并在开启自动标脏的变更上把树标记为脏。

## 5. 对话记录与管线

```csharp
public AgentTranscript Transcript { get; } = new();
```

管线是作用域替你装配的一条 `IAgentPipelineStage` 链：

```text
TextPipeline  →  SharedTools (ToolPipeline)  →  AccountingStage
```

- `TextPipeline` 把 `AgentTextDelta` / `AgentReasoningDelta` / 轮次事件折入 `AgentTranscript`（`Entries`、`ToMarkdown`、`ToPlainTextLines`）。推理会保留在答案旁，包在围栏代码块中（`AgentMarkdownOptions.ReasoningFence`，默认 `"thinking"`）。
- `SharedTools`（一个 `ToolPipeline`）编组到 UI 上下文，并在调用前强制执行三档预算。
- `AccountingStage` 把一次成功（`Succeeded`）的调用计入账本、触发回调，并在需要时把树标记为脏。被拒绝（`Refused`）或失败（`Failed`）的调用从未运行函数体，因此不计数。

**预期结果：** 一轮之后 `Transcript.Entries` 依次包含用户消息、模型的推理、它的工具调用与最终答案。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。运行对话需要真实的 `IChatClient` 与 API 密钥（demo 读取 `API_KEY_DEEPSEEK`），当前不可用。提供器缓存、管线组合与对话记录行为读自 `WorkflowAgentContextProvider.cs`、`WorkflowAgentScope.cs` 与 `AgentHelper.cs`；本页内容未做端到端执行。
