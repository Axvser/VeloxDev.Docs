# Workflow Agent — Namespace: `VeloxDev.AI.Pipelines`

The observability chain every agent run flows through, plus the transcript that renders it. `WorkflowAgentScope.Pipeline` is composed for you (`TextPipeline → ToolPipeline → AccountingStage`); `WithPipeline` / `UseAgentPipeline` attach it to the agent, and `WithTranscript` attaches the conversation. All types live in `VeloxDev.AI.Pipelines` (implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/`).

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Pipelines/*` — `AgentPipelineTests`, `AgentTranscriptTests`, `TranscriptWiringTests`) + **Demo** (`AgentHelper.ProvideAgent`).

## Events

`public abstract class AgentEvent` — base with `DateTimeOffset Timestamp { get; }`. Subclasses are `sealed`:

| Event | Carries |
|---|---|
| `AgentTurnStarted(AgentRunKind kind, string? prompt)` | `Kind`, `Prompt` |
| `AgentTurnCompleted(AgentRunKind kind, string? text, TimeSpan elapsed)` | `Kind`, `Text`, `Elapsed` |
| `AgentTurnFaulted(AgentRunKind kind, Exception? error, bool cancelled)` | `Kind`, `Error`, `Cancelled` |
| `AgentTextDelta(string text)` | `Text` |
| `AgentReasoningDelta(string text)` | `Text` |
| `AgentToolCallStarted(string toolName)` | `ToolName` |
| `AgentToolCallCompleted(string toolName, string result, AgentToolOutcome outcome, TimeSpan elapsed)` | `ToolName`, `Result`, `Outcome`, `Elapsed` |

`enum AgentRunKind` — `Complete`, `Streaming`. `enum AgentToolOutcome` — `Succeeded`, `Refused`, `Failed`.

## AgentPipeline

| Member | Signature | Notes |
|---|---|---|
| `Stages` | `IReadOnlyList<IAgentPipelineStage> { get; }` | The chain, in order. |
| `Use` | `AgentPipeline Use(IAgentPipelineStage stage)` | Appends a stage. |
| `Use` | `AgentPipeline Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` | Appends a delegate stage. |
| `PublishAsync` | `ValueTask PublishAsync(AgentEvent agentEvent, CancellationToken cancellationToken = default)` | Runs the chain. |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | Raised when a stage throws. |

`public interface IAgentPipelineStage` — `ValueTask OnEventAsync(AgentEvent agentEvent, Func<AgentEvent, ValueTask> next, CancellationToken cancellationToken)`.

`public sealed class DelegateAgentPipelineStage(…) : IAgentPipelineStage` — wraps a handler delegate.

`public sealed class AgentStageFailedEventArgs(IAgentPipelineStage stage, AgentEvent agentEvent, Exception error) : EventArgs` — `Stage`, `Event`, `Error`.

## ToolPipeline

`public sealed class ToolPipeline(Func<AgentTranscript?>? transcript = null, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage`. The scope's `SharedTools` is one instance per scope, shared by every slice.

| Member | Signature | Effect |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>? { get; set; }` | Marshals the call onto the host's context. |
| `Refuse` | `Func<string, string?>? { get; set; }` | Returns a refusal message (or `null`) before the body — the budget/host-policy gate. |
| `Confirm` | `Func<string, CancellationToken, ValueTask<string?>>? { get; set; }` | The human gate. |

## AgentTranscript

`public partial class AgentTranscript`.

| Member | Signature | Notes |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry> { get; set; }` | The conversation in order. |
| `Open` | `AgentTranscriptEntry? { get; private set; }` | The entry still being appended. |
| `CloseOpen` / `Clear` | `void …()` | Close the open entry / clear all. |
| `AddUser` / `AddError` | `AgentTranscriptEntry AddUser(string text)` / `AddError(string text)` | Append a user / error entry. |
| `AppendAnswer` / `AppendReasoning` | `AgentTranscriptEntry AppendAnswer(string fragment)` / `AppendReasoning(string fragment)` | Streaming appends. |
| `AddToolCall` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | Append a tool-call entry. |
| `ToMarkdown` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | Rich rendering. |
| `ToPlainTextLines` | `IReadOnlyList<string> ToPlainTextLines()` | One line per entry. |

`enum AgentTranscriptRole` — `User`, `Assistant`, `Reasoning`, `ToolCall`, `Error`.

`public partial class AgentTranscriptEntry` — `Text`, `Role`, `Timestamp`, `ToolName`, `Outcome` (`AgentToolOutcome?`), `Detail`, `IsStreaming`, `Summary`, `HasDetail`, plus statics `User(string)`, `Assistant()`, `Reasoning()`, `Error(string)`, `ToolCall(string, string, AgentToolOutcome)`.

`public sealed class AgentMarkdownOptions` — `ReasoningFence` (default `"thinking"`), `ReasoningHeading` (default `"**思考：**"`). Setting an empty fence turns the reasoning wrapper off; the fence length outgrows any backtick run in the body.

## Wiring extensions

`public sealed class AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline) : DelegatingAIAgent` — publishes events from both `RunCoreAsync` and `RunCoreStreamingAsync`.

`public static class AgentPipelineExtensions`:

| Member | Signature |
|---|---|
| `UseAgentPipeline` | `static AIAgentBuilder UseAgentPipeline(this AIAgentBuilder builder, AgentPipeline pipeline)` |
| `WithPipeline` | `static AIAgent WithPipeline(this AIAgent agent, AgentPipeline pipeline)` |

`public sealed class TextPipeline(Func<AgentTranscript?> transcript, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` — the stage that folds text/reasoning/turn events into the transcript. `PipelineDispatch` (internal) is the threading helper.

## Wiring

```csharp
scope.WithTranscript(transcript);                 // attach before the agent is built
var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);
```

**Expected result:** attaching the transcript before or after a subsystem still feeds it (`TranscriptWiringTests`); a stage that throws fires `StageFailed` and the earlier stages still finish.
