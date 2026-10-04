# 工作流代理 —— 命名空间：`VeloxDev.AI.Pipelines`

每次 agent 运行都会流经的可观测链，以及把它渲染出来的对话记录。`WorkflowAgentScope.Pipeline` 由作用域替你组合（`TextPipeline → ToolPipeline → AccountingStage`）；`WithPipeline` / `UseAgentPipeline` 把它挂到 agent，`WithTranscript` 挂载对话。所有类型位于 `VeloxDev.AI.Pipelines`（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/`）。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Pipelines/*` —— `AgentPipelineTests`、`AgentTranscriptTests`、`TranscriptWiringTests`）+ **Demo**（`AgentHelper.ProvideAgent`）。

## 事件

`public abstract class AgentEvent` —— 基类，带 `DateTimeOffset Timestamp { get; }`。子类皆为 `sealed`：

| 事件 | 携带 |
|---|---|
| `AgentTurnStarted(AgentRunKind kind, string? prompt)` | `Kind`、`Prompt` |
| `AgentTurnCompleted(AgentRunKind kind, string? text, TimeSpan elapsed)` | `Kind`、`Text`、`Elapsed` |
| `AgentTurnFaulted(AgentRunKind kind, Exception? error, bool cancelled)` | `Kind`、`Error`、`Cancelled` |
| `AgentTextDelta(string text)` | `Text` |
| `AgentReasoningDelta(string text)` | `Text` |
| `AgentToolCallStarted(string toolName)` | `ToolName` |
| `AgentToolCallCompleted(string toolName, string result, AgentToolOutcome outcome, TimeSpan elapsed)` | `ToolName`、`Result`、`Outcome`、`Elapsed` |

`enum AgentRunKind` —— `Complete`、`Streaming`。`enum AgentToolOutcome` —— `Succeeded`、`Refused`、`Failed`。

## AgentPipeline

| 成员 | 签名 | 说明 |
|---|---|---|
| `Stages` | `IReadOnlyList<IAgentPipelineStage> { get; }` | 按序的链。 |
| `Use` | `AgentPipeline Use(IAgentPipelineStage stage)` | 追加阶段。 |
| `Use` | `AgentPipeline Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` | 追加委托阶段。 |
| `PublishAsync` | `ValueTask PublishAsync(AgentEvent agentEvent, CancellationToken cancellationToken = default)` | 运行整条链。 |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | 某阶段抛异常时触发。 |

`public interface IAgentPipelineStage` —— `ValueTask OnEventAsync(AgentEvent agentEvent, Func<AgentEvent, ValueTask> next, CancellationToken cancellationToken)`。

`public sealed class DelegateAgentPipelineStage(…) : IAgentPipelineStage` —— 包装委托处理器。

`public sealed class AgentStageFailedEventArgs(IAgentPipelineStage stage, AgentEvent agentEvent, Exception error) : EventArgs` —— `Stage`、`Event`、`Error`。

## ToolPipeline

`public sealed class ToolPipeline(Func<AgentTranscript?>? transcript = null, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage`。作用域的 `SharedTools` 是每个作用域一个实例，被每个切片共享。

| 成员 | 签名 | 作用 |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>? { get; set; }` | 把调用编组到宿主的上下文。 |
| `Refuse` | `Func<string, string?>? { get; set; }` | 在函数体前返回拒绝消息（或 `null`）—— 预算/宿主策略闸门。 |
| `Confirm` | `Func<string, CancellationToken, ValueTask<string?>>? { get; set; }` | 人工闸门。 |

## AgentTranscript

`public partial class AgentTranscript`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry> { get; set; }` | 按序的对话。 |
| `Open` | `AgentTranscriptEntry? { get; private set; }` | 仍在追加的条目。 |
| `CloseOpen` / `Clear` | `void …()` | 关闭开放条目 / 清空。 |
| `AddUser` / `AddError` | `AgentTranscriptEntry AddUser(string text)` / `AddError(string text)` | 追加用户 / 错误条目。 |
| `AppendAnswer` / `AppendReasoning` | `AgentTranscriptEntry AppendAnswer(string fragment)` / `AppendReasoning(string fragment)` | 流式追加。 |
| `AddToolCall` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | 追加工具调用条目。 |
| `ToMarkdown` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | 富渲染。 |
| `ToPlainTextLines` | `IReadOnlyList<string> ToPlainTextLines()` | 每行一个条目。 |

`enum AgentTranscriptRole` —— `User`、`Assistant`、`Reasoning`、`ToolCall`、`Error`。

`public partial class AgentTranscriptEntry` —— `Text`、`Role`、`Timestamp`、`ToolName`、`Outcome`（`AgentToolOutcome?`）、`Detail`、`IsStreaming`、`Summary`、`HasDetail`，以及静态工厂 `User(string)`、`Assistant()`、`Reasoning()`、`Error(string)`、`ToolCall(string, string, AgentToolOutcome)`。

`public sealed class AgentMarkdownOptions` —— `ReasoningFence`（默认 `"thinking"`）、`ReasoningHeading`（默认 `"**思考：**"`）。围栏设为空则关闭推理包裹；围栏长度会超出正文中任何反引号串。

## 接线扩展

`public sealed class AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline) : DelegatingAIAgent` —— 从 `RunCoreAsync` 与 `RunCoreStreamingAsync` 两者发布事件。

`public static class AgentPipelineExtensions`：

| 成员 | 签名 |
|---|---|
| `UseAgentPipeline` | `static AIAgentBuilder UseAgentPipeline(this AIAgentBuilder builder, AgentPipeline pipeline)` |
| `WithPipeline` | `static AIAgent WithPipeline(this AIAgent agent, AgentPipeline pipeline)` |

`public sealed class TextPipeline(Func<AgentTranscript?> transcript, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` —— 把文本/推理/轮次事件折入对话记录的阶段。`PipelineDispatch`（internal）是线程辅助。

## 接线

```csharp
scope.WithTranscript(transcript);                 // 在 agent 构建前挂载
var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);
```

**预期结果：** 在子系统之前或之后挂载对话记录都会喂给它（`TranscriptWiringTests`）；抛异常的阶段触发 `StageFailed`，且更早的阶段照常完成。
