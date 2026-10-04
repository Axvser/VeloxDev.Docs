# 10.1 · 管线与对话记录

每次运行都流经一条 `AgentPipeline` —— 一串阶段。作用域替你组合一条，并用它包装 agent，因此 `RunAsync` 与 `RunStreamingAsync` 都被观察到，而宿主无需自己循环流。

```csharp
scope.WithTranscript(transcript);                 // 挂载对话记录
var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);                  // AgentPipelineExtensions.WithPipeline
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

作用域的链是 `TextPipeline → ToolPipeline (SharedTools) → AccountingStage`（先文本，后工具 —— 它们处理不相交的事件）。

## 1. 事件模型

`AgentEvent` 是基类；每个子类都是携带 `Timestamp` 的 `sealed` 记录式类：

| 事件 | 携带 |
|---|---|
| `AgentTurnStarted` | `Kind`（`AgentRunKind`）、`Prompt` |
| `AgentTurnCompleted` | `Kind`、`Text`、`Elapsed` |
| `AgentTurnFaulted` | `Kind`、`Error`、`Cancelled` |
| `AgentTextDelta` | `Text` |
| `AgentReasoningDelta` | `Text` |
| `AgentToolCallStarted` | `ToolName` |
| `AgentToolCallCompleted` | `ToolName`、`Result`、`Outcome`（`AgentToolOutcome`）、`Elapsed` |

`AgentRunKind` = `Complete` | `Streaming`。`AgentToolOutcome` = `Succeeded` | `Refused` | `Failed`。

## 2. `AgentPipeline`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Use` | `AgentPipeline Use(IAgentPipelineStage stage)` / `Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask>)` | 追加一个阶段（或委托阶段）。 |
| `Stages` | `IReadOnlyList<IAgentPipelineStage> { get; }` | 按序的链。 |
| `PublishAsync` | `ValueTask PublishAsync(AgentEvent agentEvent, CancellationToken = default)` | 运行整条链。 |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | 某阶段抛异常时触发。 |

阶段实现 `IAgentPipelineStage.OnEventAsync(AgentEvent, Func<AgentEvent, ValueTask> next, CancellationToken)`。阶段可以为它**之后**的阶段**丢弃**事件（不调用 `next`），但无法抹去之前已发生的。抛异常的阶段**不**中断运行 —— `StageFailed` 触发，之前的阶段照常完成。来源：`AgentPipelineTests.AStageMayDropAnEvent_…`、`AStageThatThrows_…`。

`AgentPipelineAgent : DelegatingAIAgent` 包装内部 agent，并从 `RunCoreAsync` 与 `RunCoreStreamingAsync` 两者发布事件。`AgentPipelineExtensions.WithPipeline(this AIAgent, AgentPipeline)`（以及 `UseAgentPipeline(this AIAgentBuilder, …)`）是接线。

**预期结果：** 用 `Use` 添加的两个阶段按序运行（测试中为 `["first","second","third"]`）；过滤掉推理的阶段让对话记录少一条条目。

## 3. `ToolPipeline` —— 工具运行其后的闸门

`ToolPipeline` 自身就是一个阶段，作用域的 `SharedTools` 是每个切片（内置、MCP、技能、子代理）共享的同一个实例。它的钩子实时读取作用域：

| 成员 | 签名 | 作用 |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>?` | 把调用编组到宿主的 UI 上下文。 |
| `Refuse` | `Func<string, string?>?` | 在函数体运行前返回拒绝消息（或 `null`）—— 预算/宿主策略闸门。 |
| `Confirm` | `Func<string, CancellationToken, ValueTask<string?>>?` | 人工闸门（`WithToolApproval`）。 |

由于每个作用域**只有一个实例**，`Refuse` 与 `Confirm` 触达 MCP 或技能来源的工具，正如触达内置工具一样：开关或预算不可能在一条路径上生效而在另一条上被忽略。

## 4. `AgentTranscript` —— 对话

| 成员 | 签名 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry> { get; set; }` | 按序的对话。 |
| `Open` | `AgentTranscriptEntry? { get; private set; }` | 仍在追加的条目。 |
| `AddUser` / `AddError` | `AgentTranscriptEntry AddUser(string text)` / `AddError(string)` | 追加用户 / 错误条目。 |
| `AppendAnswer` / `AppendReasoning` | `AgentTranscriptEntry AppendAnswer(string fragment)` / `AppendReasoning(string)` | 流式追加（累积到一个条目）。 |
| `AddToolCall` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | 追加工具调用条目。 |
| `ToMarkdown` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | 为富面板渲染。 |
| `ToPlainTextLines` | `IReadOnlyList<string> ToPlainTextLines()` | 每行一个条目（工具行携带工具名 + 结果）。 |

`AgentTranscriptEntry` 有 `Role`（`AgentTranscriptRole`：`User`、`Assistant`、`Reasoning`、`ToolCall`、`Error`）、`Text`、`Summary`、`Detail`（仅工具调用）、`Outcome`、`Timestamp`、`IsStreaming`。推理渲染在**围栏代码块**内（默认 ```thinking），使 Markdown 控件把它画成独立块，而非折进答案。`AgentMarkdownOptions.ReasoningFence` / `ReasoningHeading` 可改；围栏长度会超出正文中任何反引号串。

**预期结果：** 一轮之后 `Transcript.Entries` 为 用户 → 推理 → 助手（不推理的模型不产生推理条目）；连续工具调用渲染为一个块，而非空的分隔线。

## 运行声明

- ✅ 实际构建并运行 —— 确定性 agent 测试套件（2026-10-01，`已通过! 失败: 0，通过: 387`）包含 `Pipelines/**`（`AgentPipelineTests`、`AgentTranscriptTests`、`TranscriptWiringTests`），覆盖阶段顺序、事件丢弃、失败隔离、对话记录角色与 markdown 围栏。它们运行在离线的脚本化 `IChatClient` 上，而非真实模型。
