# General agent extensions

These `VeloxDev.AI` helpers apply outside the workflow layer. They compose with the same providers, policies and pipeline as a workflow scope.

## Class: AgentClientExtensions

| Member | Signature | Description |
|---|---|---|
| `AsAIAgent` | `static ChatClientAgent AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` | Creates an agent whose instructions are the given static skeleton and whose tools come entirely from `providers`. There is deliberately no tools parameter: the framework unions provider tools with `ChatOptions.Tools` without deduplicating, so leaving the parameter out makes that mistake unavailable. |

```csharp
var agent = chatClient.AsAIAgent([mcp.CreateContextProvider()]);
```

## Class: AgentObjectToolkit

`VeloxDev.AI.AgentObjectToolkit : IAgentToolCallNotifier` wraps an arbitrary .NET object as MAF-compatible tools, using the compiled context tree, generated accessors, `TypeIntrospector` and `ComponentPatcher`. It is the generic, non-workflow counterpart of `WorkflowAgentToolkit`.

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `AgentObjectToolkit(object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | Exposes `target`; `rejectedProperties` names properties the patch tool must refuse. |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | Raised after each successful call. Refusals and failures travel on `Pipeline` as `AgentToolCallCompleted`. |
| `MaxToolCalls` | `int?` | Call ceiling; `null` means unlimited. |
| `CreateTools()` | `IList<AITool> CreateTools()` | Creates all generic tools, wrapped so `ToolCalled` fires and the pipeline reports. |
| `Pipeline` | `AgentPipeline` | The toolkit's event chain, created on first use. |
| `Tools` | `ToolPipeline` | The tool seam handed to every wrapper: one call ceiling and one reporting point. Registers no thread marshalling by design, because the wrapped target is an arbitrary object rather than a UI-bound component. |

A type the generator did not admit still gets the ten tools, but each answers that the type is not in the tree. That closed world is what makes the surface trimmable.

## Class: AgentObjectToolkitExtensions

| Member | Signature | Description |
|---|---|---|
| `AsAgentToolkit` | `static AgentObjectToolkit AsAgentToolkit(this object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | Creates a toolkit over any object. |
| `AsAgentTools` | `static IList<AITool> AsAgentTools(this object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | Convenience: creates the toolkit and returns all tools. |

## Class: AgentTelemetryExtensions

Turns on the Agent Framework's own OpenTelemetry instrumentation. The library emits no telemetry of its own; `AgentTranscript` and `AgentPipeline` are the host-facing surface, and neither leaves the process.

| Member | Signature | Description |
|---|---|---|
| `UseAgentTelemetry` | `static AIAgentBuilder UseAgentTelemetry(this AIAgentBuilder builder, string? sourceName = null, bool enableSensitiveData = false)` | Instruments every run the agent builds. Prefer this over wrapping a finished agent; the source name must also be registered with the host's `TracerProvider` / `MeterProvider`. |
| `WithAgentTelemetry` | `static AIAgent WithAgentTelemetry(this AIAgent agent, string? sourceName = null, bool enableSensitiveData = false)` | Instruments directly, for callers not using a builder. |

`enableSensitiveData` defaults to `false` and should stay so outside development: with it on, spans carry the full conversation text, including tool results.

## Related

- [WorkflowAgentScope](../00_workflow-agent-scope/index.md) — the workflow counterpart of these helpers.
- [Agent Dashboard and Transcript](../../22_agent-dashboard-transcript/01_event-pipeline/index.md) — the library's own observation surface.
