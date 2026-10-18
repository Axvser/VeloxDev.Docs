# 05 · 运行一轮对话

这是真正涉及模型的一页。此前的一切都是离线配置。

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
}).WithPipeline(scope.Pipeline);                                  // 观察 Run 与 RunStreaming

var session = await agent.CreateSessionAsync();
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

这里有两条关键规则：

- **上下文提供器是工具的唯一来源。** Agent Framework 会把提供器贡献的工具与 `ChatOptions.Tools` 里的工具合并，而该合并不按名字去重。同时经两条通道提供同一工具会让模型收到两次。因此让 `ChatOptions.Tools` 保持为空 —— 提供器才是渲染工具列表的地方。
- **在 agent 存在之前挂载对话记录。** 作用域在那一刻从对话记录组合出阶段链；agent 随之被该链包裹。

便捷重载 `AgentClientExtensions.AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` 做同样的事，无需展开 `ChatClientAgentOptions`。

**预期结果：** `agent` 是 `AIAgent`，`session` 创建成功；当 `chatClient` 是真实模型客户端时，此时还不会发起网络调用。

## 2. 提供器每轮渲染

`WorkflowAgentContextProvider`（`scope.CreateContextProviders()` 之一）让挂载、关闭或加载某样东西在**下一轮**生效，而无需重建 agent。它以 `scope.ContextKey`（作用域 `Version`、树的当前选中集 revision 与预算用量档）键控缓存渲染：

- 在**未变化**的一轮，它不加锁、不分配 —— 返回上次返回的同一个 `AIContext` 实例。
- 在变化的一轮，它重建指令（`BuildDynamicInstructions`），并在作用域 `Version` 移动时重建工具列表（`BuildDynamicTools`）。

`CreateContextProviders()` 以**固定**顺序组装（因此 `With*` 的调用顺序不会改变提示的读法）：

1. 若调用了 `WithContextCompaction`，压缩提供器；
2. 本作用域自己的 `WorkflowAgentContextProvider`；
3. 技能提供器（若 `WithSkills`）；
4. MCP 提供器（若 `WithMcps`）；
5. 子代理名册提供器（若 `WithSubAgents`）；
6. 框架的 todo 提供器（若 `WithTodoTracking`）与模式提供器（若 `WithAgentModes`）；
7. 每个经 `WithContextProvider` 注册的工厂。

**预期结果：** 配置未变时连续调用提供器两次返回同一个 `AIContext` 实例；两次之间调用 `SetToolEnabled(...)` 会让第二次渲染出新实例。

## 3. 可选的框架脚手架

```csharp
scope.WithTodoTracking()                     // 框架的 todos_* 工具 + 未完成工作提示
     .WithAgentModes(new AgentModeProviderOptions { /* Modes = [...], DefaultMode = "build" */ })
     .WithContextCompaction(maxContextWindowTokens: 128_000, maxOutputTokens: 8_192);
```

- `WithTodoTracking(options?)` 启用框架的 todo 列表；`todos_*` 工具来自框架自己的提供器，刻意**不**按 workflow 工具的方式包装（它们既不读也不写树）。
- `WithAgentModes(options)` 添加 `mode_set` / `mode_get` 工具。`options` 是必需的 —— 没有有用的默认值。属性 `AgentMode` 让宿主切换模式。
- `WithContextCompaction(maxContextWindowTokens, maxOutputTokens)` 限制对话长度：超过阈值后最旧的工具结果被摘要，再超过下一个阈值后最旧的轮次被丢弃。**这两个数字是关于宿主模型的事实** —— 传真实上下文窗口与输出上限，而不是猜测（示例正是因此省略了这次调用）。

**预期结果：** 调用 `WithTodoTracking` 后模型会拿到框架的 `todos_*` 工具；这些调用不消耗 workflow 预算，也不把树标脏。

## 4. 发送一轮

```csharp
AgentResponse response = await agent.RunAsync("Add a node of type Demo.ViewModels.NetworkRequest and wire it to the existing controller.", session);
Console.WriteLine(response.Text);
```

**预期结果：** 模型作答；若它决定行动，对话记录会按顺序增加 `ToolCall` 条目；每次工具调用都在 UI 线程上运行（若注册了 `SynchronizationContext`）、计入预算，并在自动标脏开启时对变更标脏。

## 5. 对话记录与管线

```csharp
public AgentTranscript Transcript { get; } = new();
```

管线是作用域替你组装的一串 `IAgentPipelineStage`：

```text
TextPipeline  →  SharedTools (ToolPipeline)  →  AccountingStage
```

- `TextPipeline` 把 `AgentTextDelta` / `AgentReasoningDelta` / 轮次事件折进 `AgentTranscript`（`Entries`、`ToMarkdown`、`ToPlainTextLines`）。推理内容保留在答案旁边，包在围栏代码块里（`AgentMarkdownOptions.ReasoningFence`，默认 `"thinking"`）。
- `SharedTools`（一个 `ToolPipeline`）编组到 UI 上下文，并在调用前执行三档调用预算。
- `AccountingStage` 把完成的 `Succeeded` 调用计入账本、触发回调，并在需要时标脏。`Refused` 或 `Failed` 的调用从未运行函数体，因此不计数。

**预期结果：** 一轮之后 `Transcript.Entries` 按顺序包含用户消息、模型推理、它的工具调用与最终答案。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验（2026-10-18）。运行对话需要真实 `IChatClient` 与 API key（示例读取 `API_KEY_DEEPSEEK`），当前不可用。提供器缓存、管线组合与对话记录行为读自 `WorkflowAgentContextProvider.cs`、`WorkflowAgentScope.cs` 与 `AgentHelper.cs`；本页没有任何内容被端到端执行。
