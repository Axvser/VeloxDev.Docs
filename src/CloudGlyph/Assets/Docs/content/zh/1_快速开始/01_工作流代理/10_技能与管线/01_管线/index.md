# 10.1 · 管线与对话记录

每次运行都流经一个 `AgentPipeline` —— 一条阶段链。作用域替你组合一条并用它包裹 agent，因此 `RunAsync` 与 `RunStreamingAsync` 都被观察，宿主无需自己循环读取流。

```csharp
scope.WithTranscript(transcript);                 // 挂载对话
var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);                  // AgentPipelineExtensions.WithPipeline
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

作用域的链是 `TextPipeline → ToolPipeline (SharedTools) → AccountingStage`（文本在前，工具在后 —— 它们处理不相交的事件）。

## 1. 事件模型

`AgentEvent` 是基类；每个子类都是 `sealed` 的类记录，携带 `Timestamp`：

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
| `Use` | `AgentPipeline Use(IAgentPipelineStage stage)` / `Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask>)` | 追加阶段（或委托阶段）。 |
| `Stages` | `IReadOnlyList<IAgentPipelineStage> { get; }` | 按顺序的阶段链。 |
| `PublishAsync` | `ValueTask PublishAsync(AgentEvent agentEvent, CancellationToken = default)` | 运行整条链。 |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | 阶段抛异常时触发。 |

阶段实现 `IAgentPipelineStage.OnEventAsync(AgentEvent, Func<AgentEvent, ValueTask> next, CancellationToken)`。阶段可以**丢弃**给**其后**阶段的事件（不调用 `next`），但无法撤销之前发生的事。抛异常的阶段**不会**中断运行 —— `StageFailed` 触发，之前的阶段照常完成。来源：`AgentPipelineTests.AStageMayDropAnEvent_…`、`AStageThatThrows_…`。

`AgentPipelineAgent : DelegatingAIAgent` 包裹内层 agent，并从 `RunCoreAsync` 与 `RunCoreStreamingAsync` 两者发布事件。连接方式是 `AgentPipelineExtensions.WithPipeline(this AIAgent, AgentPipeline)`（以及 `UseAgentPipeline(this AIAgentBuilder, …)`）。

**预期结果：** 用 `Use` 加两个阶段会按顺序运行（测试中为 `["first","second","third"]`）；过滤推理的阶段会让对话记录少一个条目。

## 3. `ToolPipeline` —— 工具运行其后的闸门

`ToolPipeline` 本身是一个阶段，作用域的 `SharedTools` 是每个切片（内置、MCP、技能、子代理）共享的同一实例。它的钩子实时读取作用域：

| 成员 | 签名 | 效果 |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>?` | 把调用编组到宿主的 UI 上下文。 |
| `Refuse` | `Func<string, string?>?` | 在函数体运行前返回拒绝消息（或 `null`）—— 预算/宿主策略闸门。 |
| `Confirm` | `Func<string, CancellationToken, ValueTask<string?>>?` | 人工/权限闸门（`PermissionPolicy.Evaluate`）。 |

因为**每个作用域只有一个实例**，`Refuse` 与 `Confirm` 触达 MCP 或技能来源的工具的方式，与触达内置工具完全相同：一个开关、预算或 `Deny` 不可能在一条路径上生效、在另一条上被忽略。

## 4. `AgentTranscript` —— 对话

| 成员 | 签名 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry> { get; set; }` | 按顺序的对话。 |
| `Open` | `AgentTranscriptEntry? { get; private set; }` | 仍在追加的条目。 |
| `AddUser` / `AddError` | `AgentTranscriptEntry AddUser(string text)` / `AddError(string)` | 追加用户 / 错误条目。 |
| `AppendAnswer` / `AppendReasoning` | `AgentTranscriptEntry AppendAnswer(string fragment)` / `AppendReasoning(string)` | 流式追加（累积进一个条目）。 |
| `AddToolCall` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | 追加工具调用条目。 |
| `ToMarkdown` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | 为富面板渲染。 |
| `ToPlainTextLines` | `IReadOnlyList<string> ToPlainTextLines()` | 每条目一行（工具行带工具名 + 结果）。 |

`AgentTranscriptEntry` 有 `Role`（`AgentTranscriptRole`：`User`、`Assistant`、`Reasoning`、`ToolCall`、`Error`）、`Text`、`Summary`、`Detail`（仅工具调用）、`Outcome`、`Timestamp`、`IsStreaming`。推理内容渲染在**围栏代码块内**（默认 ```thinking），让 Markdown 控件把它画成独立块，而不是折进答案。`AgentMarkdownOptions.ReasoningFence` / `ReasoningHeading` 可改；围栏长度会超过正文中的任何反引号串。

**预期结果：** 一轮之后 `Transcript.Entries` 读作 User → Reasoning → Assistant（不推理的模型不产生 Reasoning 条目）；连续工具调用渲染成一个块，而不是空分隔线。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。`Pipelines/**` 测试存在且在 2026-10-01 的一次记录运行（387 项）中通过，但该运行早于权限模式重构，不作为当前证据。
