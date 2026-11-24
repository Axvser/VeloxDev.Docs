# Event pipeline

The pipeline is the library's event vocabulary and stage chain: it observes what a run did and turns it into transcript entries, without changing the run. It sits in the Agent Framework's official middleware slot, so a host keeps calling `RunAsync` / `RunStreamingAsync` unchanged.

## Scope members

| Member | Signature | Description |
|---|---|---|
| `Pipeline` | `AgentPipeline Pipeline { get; }` | The scope's event chain, composed on first use and shared. |

Attach the pipeline with `scope.WithTranscript(...)` (which composes the accounting and transcript stages) or with `agent.AsBuilder().UseAgentPipeline(scope.Pipeline).Build()`.

## Base class: AgentEvent

| Member | Type | Description |
|---|---|---|
| `Timestamp` | `DateTimeOffset` | When the pipeline observed the event. |

Events are observations, not control flow: a stage may drop or rewrite them, but the run is driven by the agent.

### Event types

| Type | Carries |
|---|---|
| `AgentTurnStarted` | `Kind`, `Prompt`, `Attachments`. Constructors take `(AgentRunKind, string?)` or `(AgentRunKind, string?, IReadOnlyList<AgentAttachment>?)`. |
| `AgentTurnCompleted` | `Kind`, `Text` (null when streaming), `Elapsed`, `Usage`. Constructor `(AgentRunKind, string?, TimeSpan, UsageDetails?)`. |
| `AgentUsageReported` | `Usage` — token counts reported during a streaming run. |
| `AgentTurnFaulted` | `Kind`, `Error` (null when cancelled), `Cancelled`. |
| `AgentTextDelta` | `Text` — a raw fragment of the answer. |
| `AgentReasoningDelta` | `Text` — a raw fragment of the model's thinking. |
| `AgentToolCallStarted` | `ToolName`. |
| `AgentToolCallCompleted` | `ToolName`, `Result`, `Outcome`, `Elapsed`. |
| `AgentMediaReceived` | `Attachment`, `Content` — the model produced non-text media. |

Reasoning is recovered from `TextReasoningContent`. `AgentResponseUpdate.Text` concatenates only the answer, which is why reading it alone loses the thinking.

## Enums

| `AgentRunKind` | Meaning |
|---|---|
| `Complete` | Produced by `RunAsync`; one whole response. |
| `Streaming` | Produced by `RunStreamingAsync`; fragments. |

| `AgentToolOutcome` | Meaning |
|---|---|
| `Succeeded` | The tool ran and returned. |
| `Refused` | A stage refused the call before it ran; `Result` carries the refusal. |
| `Failed` | The tool threw; the wrapper turns it into an error result so the run continues. |

## Interface: IAgentPipelineStage

| Member | Signature | Description |
|---|---|---|
| `OnEventAsync` | `ValueTask OnEventAsync(AgentEvent agentEvent, Func<AgentEvent, ValueTask> next, CancellationToken cancellationToken)` | Sees every event and decides what the next stage sees: pass it on, drop it, replace it, or emit more than one. |

`DelegateAgentPipelineStage(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` is the adapter for a delegate.

## Class: AgentPipeline

| Member | Type / Signature | Description |
|---|---|---|
| `Stages` | `IReadOnlyList<IAgentPipelineStage>` | The stages, in order. |
| `Use(IAgentPipelineStage stage)` | `AgentPipeline Use(IAgentPipelineStage stage)` | Appends a stage; returns this. |
| `Use(Func<...> handler)` | `AgentPipeline Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` | Appends a delegate stage. |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | Raised when a stage throws. Publishing carries on regardless. |
| `PublishAsync(AgentEvent agentEvent, CancellationToken cancellationToken = default)` | `ValueTask PublishAsync(...)` | Sends an event through every stage in order. |

A broken stage does not break the run: each stage is isolated, a failure skips the rest of the chain and surfaces on `StageFailed`. A stage that merely draws something must not turn a successful tool call into an error result.

`AgentStageFailedEventArgs` carries `Stage`, `Event` and `Error`.

## Class: AgentPipelineAgent

`AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline) : DelegatingAIAgent` sits in MAF's middleware slot and publishes the run's events. It yields updates unchanged and unbuffered, so stream timing is preserved.

| Member | Signature |
|---|---|
| Constructor | `AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline)` |
| RunCoreAsync | `protected override Task<AgentResponse> RunCoreAsync(IEnumerable<ChatMessage> messages, AgentSession? session = null, AgentRunOptions? options = null, CancellationToken cancellationToken = default)` |
| RunCoreStreamingAsync | `protected override IAsyncEnumerable<AgentResponseUpdate> RunCoreStreamingAsync(IEnumerable<ChatMessage> messages, AgentSession? session = null, AgentRunOptions? options = null, CancellationToken cancellationToken = default)` |

### Class: AgentPipelineExtensions

| Method | Signature | Description |
|---|---|---|
| `UseAgentPipeline` | `static AIAgentBuilder UseAgentPipeline(this AIAgentBuilder builder, AgentPipeline pipeline)` | Wraps the built agent in the middleware slot. |
| `WithPipeline` | `static AIAgent WithPipeline(this AIAgent agent, AgentPipeline pipeline)` | Wraps an existing agent directly. |

## Class: TextPipeline

`TextPipeline(Func<AgentTranscript?> transcript, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` turns streamed output into answer and reasoning entries. It coalesces fragments before writing, so a long answer costs linear rather than quadratic work. The events themselves are untouched; only the transcript write is batched.

## Class: ToolPipeline

`ToolPipeline(Func<AgentTranscript?>? transcript = null, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` holds the gates consulted before a call and the entries written after it.

| Member | Type | Description |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>?` | The thread the call is marshalled onto, read once per call. |
| `Refuse` | `Func<ToolInvocation, string?>?` | Consulted before a call; a message refuses it. Budgets and permissions are decided here. |
| `Confirm` | `Func<ToolInvocation, CancellationToken, ValueTask<string?>>?` | Consulted after `Refuse` and before the call; a message refuses it. Runs inside the marshalled block so a dialog is on the right thread. |
| `MaxResultChars` | `Func<int?>?` | Per-call result-size cap; null or 0 means no cap. |
| `MutationGate` | `Func<SemaphoreSlim?>?` | Serializes graph-mutating calls across scopes on one tree; queries do not acquire it. |

## Related

- [Transcript](../00_transcript/index.md) — what the built-in stages write into.
- [Dashboard](../02_dashboard/index.md) — the panel over the same scope.
