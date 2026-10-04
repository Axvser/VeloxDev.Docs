# 10.1 · Pipelines & Transcript

Every run flows through an `AgentPipeline` — a chain of stages. The scope composes one for you and wraps the agent with it, so both `RunAsync` and `RunStreamingAsync` are observed without the host looping the stream itself.

```csharp
scope.WithTranscript(transcript);                 // attach the conversation
var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);                  // AgentPipelineExtensions.WithPipeline
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

The scope's chain is `TextPipeline → ToolPipeline (SharedTools) → AccountingStage` (text first, then tools — they handle disjoint events).

## 1. The event model

`AgentEvent` is the base; every subclass is a `sealed` record-like class carrying `Timestamp`:

| Event | Carries |
|---|---|
| `AgentTurnStarted` | `Kind` (`AgentRunKind`), `Prompt` |
| `AgentTurnCompleted` | `Kind`, `Text`, `Elapsed` |
| `AgentTurnFaulted` | `Kind`, `Error`, `Cancelled` |
| `AgentTextDelta` | `Text` |
| `AgentReasoningDelta` | `Text` |
| `AgentToolCallStarted` | `ToolName` |
| `AgentToolCallCompleted` | `ToolName`, `Result`, `Outcome` (`AgentToolOutcome`), `Elapsed` |

`AgentRunKind` = `Complete` | `Streaming`. `AgentToolOutcome` = `Succeeded` | `Refused` | `Failed`.

## 2. `AgentPipeline`

| Member | Signature | Notes |
|---|---|---|
| `Use` | `AgentPipeline Use(IAgentPipelineStage stage)` / `Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask>)` | Appends a stage (or a delegate stage). |
| `Stages` | `IReadOnlyList<IAgentPipelineStage> { get; }` | The chain, in order. |
| `PublishAsync` | `ValueTask PublishAsync(AgentEvent agentEvent, CancellationToken = default)` | Runs the chain. |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | Raised when a stage throws. |

A stage implements `IAgentPipelineStage.OnEventAsync(AgentEvent, Func<AgentEvent, ValueTask> next, CancellationToken)`. A stage may **drop** an event for the stages **after** it (by not calling `next`) but cannot unwrite what came before. A stage that throws does **not** break the run — `StageFailed` fires and the earlier stages finish. Source: `AgentPipelineTests.AStageMayDropAnEvent_…`, `AStageThatThrows_…`.

`AgentPipelineAgent : DelegatingAIAgent` wraps the inner agent and publishes events from both `RunCoreAsync` and `RunCoreStreamingAsync`. `AgentPipelineExtensions.WithPipeline(this AIAgent, AgentPipeline)` (and `UseAgentPipeline(this AIAgentBuilder, …)`) is the wiring.

**Expected result:** two stages added with `Use` run in order (`["first","second","third"]` in the test); a stage that filters reasoning leaves one fewer entry in the transcript.

## 3. `ToolPipeline` — the gate the tools run behind

`ToolPipeline` is itself a stage, and the scope's `SharedTools` is one instance shared by every slice (built-ins, MCP, skills, sub-agents). Its hooks read the scope live:

| Member | Signature | Effect |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>?` | Marshals the call onto the host's UI context. |
| `Refuse` | `Func<string, string?>?` | Returns a refusal message (or `null`) before the body runs — the budget/host-policy gate. |
| `Confirm` | `Func<string, CancellationToken, ValueTask<string?>>?` | The human gate (`WithToolApproval`). |

Because there is **one instance per scope**, `Refuse` and `Confirm` reach an MCP- or skill-sourced tool exactly as they reach a built-in: a switch or budget cannot be honoured on one path and ignored on another.

## 4. `AgentTranscript` — the conversation

| Member | Signature | Notes |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry> { get; set; }` | The conversation in order. |
| `Open` | `AgentTranscriptEntry? { get; private set; }` | The entry still being appended. |
| `AddUser` / `AddError` | `AgentTranscriptEntry AddUser(string text)` / `AddError(string)` | Appends a user / error entry. |
| `AppendAnswer` / `AppendReasoning` | `AgentTranscriptEntry AppendAnswer(string fragment)` / `AppendReasoning(string)` | Streaming appends (accumulate into one entry). |
| `AddToolCall` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | Appends a tool-call entry. |
| `ToMarkdown` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | Renders for a rich panel. |
| `ToPlainTextLines` | `IReadOnlyList<string> ToPlainTextLines()` | One line per entry (tool lines carry the tool name + outcome). |

`AgentTranscriptEntry` has `Role` (`AgentTranscriptRole`: `User`, `Assistant`, `Reasoning`, `ToolCall`, `Error`), `Text`, `Summary`, `Detail` (tool calls only), `Outcome`, `Timestamp`, `IsStreaming`. Reasoning is rendered **inside a fenced code block** (default ```thinking) so a Markdown control draws it as a block of its own rather than folding it into the answer. `AgentMarkdownOptions.ReasoningFence` / `ReasoningHeading` change that; the fence outgrows any backtick run in its body.

**Expected result:** after one turn, `Transcript.Entries` reads User → Reasoning → Assistant (a model that does not reason produces no Reasoning entry); consecutive tool calls render as one block, not blank rules.

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite (2026-10-01, `已通过! 失败: 0，通过: 387`) includes `Pipelines/**` (`AgentPipelineTests`, `AgentTranscriptTests`, `TranscriptWiringTests`), covering stage order, event dropping, failure isolation, the transcript roles and the markdown fence. Those run over an offline scripted `IChatClient`, not a live model.
