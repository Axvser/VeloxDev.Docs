# WorkflowAgentScope

`VeloxDev.AI.Workflow.WorkflowAgentScope` configures and runs an agent over one workflow tree. It holds the tree, the tool surface, the call session and the context-provider chain. Every `With*` method returns the same scope, so a host configures it as one fluent chain.

Members that belong to another feature are documented there: permission and budget members in [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md), prompt and skill members in [Agent Context and Skills](../../19_agent-context-skills/index.md), `WithMcps` / `Mcp` in [MCP Integration](../../20_mcp-integration/index.md), `WithSubAgents` / `SubAgents` in [Sub-Agents](../../21_sub-agents/index.md), and `WithTranscript` / `Transcript` / `Pipeline` in [Agent Dashboard and Transcript](../../22_agent-dashboard-transcript/index.md).

## Creation

`AsAgentScope()` is the extension `AgentEx.AsAgentScope(this ITreeComponent)`.

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope();
```

The scope wraps the tree; it does not copy or replace it.

## Properties

| Name | Type | Description |
|---|---|---|
| `Tree` | `ITreeComponent` | The workflow tree this scope operates on. Replaced by `LoadWorkflow`. |
| `Version` | `long` | Monotonic version of everything the scope can be configured with. Every setter that changes what the agent is shown advances it, so a provider caching on it re-renders only on a real change. |
| `MaxToolResultChars` | `int` | Cap on one tool result's text. Over the cap, the result is replaced by a truncation envelope. Defaults to 64 KiB; `0` disables the cap. |
| `MaxTokens` | `int?` | Session token cap, or `null` for none. Enforced in every mode, including `Bypass`. |
| `MaxToolCalls` | `int?` | Total tool-call cap, or `null` for none. Not counted or enforced in `Bypass`. |
| `InputTokens` / `OutputTokens` / `TotalTokens` | `long` | Provider-reported spend for this scope's runs. |
| `CheckpointStore` | `IExecutionCheckpointStore?` | Where compiled runs write their place down. `null` keeps an in-memory store owned by the scope. |
| `Todo` | `TodoProvider?` | The Agent Framework todo list, once `WithTodoTracking` attached it. |
| `AgentMode` | `AgentModeProvider?` | The Agent Framework operating mode, once `WithAgentModes` attached it. |
| `PromptLanguage` | `AgentLanguages` | Prompt language set by `WithPromptLanguage`. |

## Events

| Name | Type | Description |
|---|---|---|
| `Changed` | `EventHandler` | Raised whenever something the agent is shown changes — a `With*` call, a tool switch, an attached subsystem. Raised on the changing thread, with no marshalling. |
| `TreeChanged` | `EventHandler` | Raised after `LoadWorkflow` replaces the scope's tree. |
| `ToolCalled` | `EventHandler<AgentToolCallEventArgs>` | Raised after a **successful** tool call. Refused and failed calls are published on `Pipeline` as `AgentToolCallCompleted`. |

## Tool registration

| Method | Description |
|---|---|
| `WorkflowAgentScope WithTools(string? promptContext, params AITool[] tools)` | Registers mutation-capable custom tools, merged into `ProvideTools`. Each `AIFunction` is wrapped so it receives UI-thread marshalling, accounting, the call callback and optional dirty marking. |
| `WorkflowAgentScope WithQueryTools(string? promptContext, params AITool[] tools)` | Registers read-only custom tools. They behave like `WithTools` but never auto-mark the tree dirty. |
| `IList<AITool> ProvideTools()` | Convenience snapshot of all tools. Prefer `CreateToolkit().CreateTools()` when the set must follow later changes. |
| `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | Snapshot of the selected category groups. Custom tools are always included. |
| `WorkflowAgentToolkit CreateToolkit()` | The scope's single toolkit, created on first use. It owns the call ledger and snapshot history, so one instance is shared by every caller. |
| `WorkflowAgentScope WithToolEnabled(string toolName, bool enabled = true)` | Switches one tool off or on by name. A disabled tool is not offered from the next turn on. |
| `bool SetToolEnabled(string toolName, bool enabled)` | Runtime counterpart of `WithToolEnabled`; advances `Version` and returns whether the switch moved. |
| `bool IsToolEnabled(string toolName)` | Whether the named tool is currently offered. |
| `IReadOnlyList<string> DisabledToolNames` | Snapshot of the switched-off tool names. |

`WithTools` keeps the custom tool's prompt text so the provider can inject it. A non-`AIFunction` tool is added unwrapped and receives none of the tracking; wrap it with the SDK's `AsAIFunction()` to opt in.

## Session wiring

| Method | Description |
|---|---|
| `WorkflowAgentScope WithWorkflowLoader(Func<string, ITreeComponent> loader)` | Supplies the loader `LoadWorkflow` uses. The host should rebind its surface when `TreeChanged` fires. |
| `ITreeComponent LoadWorkflow(string json)` | Replaces the tree with a deserialized graph. The old tree is left untouched; the host owns closing it. |
| `WorkflowAgentScope WithSynchronizationContext(SynchronizationContext? context)` | Marshals every tool call onto the UI thread. Workflow components are UI-bound, so mutations must run on the binding thread; pass `SynchronizationContext.Current` during setup. |
| `WorkflowAgentScope WithLogWriter(ILogWriter? writer)` | Sends a compiled run's log lines to a sink as well as the in-memory session log. |
| `WorkflowAgentScope WithCheckpointStore(IExecutionCheckpointStore? store)` | Sets where compiled runs write checkpoints; `null` restores the in-memory store. |
| `WorkflowAgentScope WithSessionConfiguration(Action<RuntimeContext> configure)` | Configures the `RuntimeContext` a compiled run uses — retry policy, observer, error sink, compensator, gate, checkpoint store, log writer. Called after the scope's own settings and before the toolkit's. |
| `WorkflowAgentScope WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | Registers the handler for successful calls. Replaces any previous one. |
| `bool TryStopRun(IRuntimeContext context)` | Asks a background compiled run, identified by the session the host configured, to stop. Returns `false` for a run this scope does not hold. |

`WithSynchronizationContext` is required for any bound UI: without it, tools run on whatever thread the chat client invokes them on.

## Providers and runtime extras

| Method | Description |
|---|---|
| `AIContextProvider CreateContextProvider()` | Creates the workflow context provider — the object that renders prompt text and the full tool set per invocation. |
| `IReadOnlyList<AIContextProvider> CreateContextProviders()` | Creates every provider to attach, in fixed order: compaction (if configured), the workflow provider, then one per attached subsystem (skills, MCP, sub-agents), then one per `WithContextProvider` factory. Pass the result to `ChatClientAgentOptions.AIContextProviders`. |
| `WorkflowAgentScope WithContextProvider(Func<WorkflowAgentScope, AIContextProvider> factory)` | Adds one provider factory. Factories run once, in registration order. Do not contribute tool names the scope already offers — the framework unions without deduplicating. |
| `WorkflowAgentScope WithContextCompaction(int maxContextWindowTokens, int maxOutputTokens)` | Bounds conversation history: old tool results are summarized and old turns dropped as the window fills. Pass the host model's real context window and output cap. |
| `WorkflowAgentScope WithTodoTracking(TodoProviderOptions? options = null)` | Adds the Agent Framework todo tools and a per-turn outstanding-work briefing. These tools are not wrapped: they neither touch the tree nor spend the call budget. |
| `WorkflowAgentScope WithAgentModes(AgentModeProviderOptions options)` | Adds the Agent Framework `mode_set` / `mode_get` tools. The modes and the starting mode are the host's choice. |
| `ValueTask DisposeAsync()` | Cancels and awaits running sub-agents and tears down every MCP connection. Safe to call more than once. |

`CreateContextProviders` fixes the order rather than following attachment order, because the framework concatenates contributions — attachment order would otherwise decide how the prompt reads.

## Class: WorkflowAgentContextProvider

`VeloxDev.AI.Workflow.WorkflowAgentContextProvider : AIContextProvider` renders the scope's current skills, prompt text and full tool set on every invocation. It is the sole source of tools: leave `ChatOptions.Tools` empty, because the framework unions provider tools with that list without deduplicating by name.

| Member | Signature | Description |
|---|---|---|
| Constructor | `WorkflowAgentContextProvider(WorkflowAgentScope scope)` | Binds the provider to a scope; throws `ArgumentNullException` when null. |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | Per-scope keys, so two trees with their own scopes do not collide. |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | Renders the per-turn contribution. |

The rendered result is cached on the scope's `Version`; an unchanged turn allocates nothing and returns the previous render.

## Related

- [WorkflowAgentToolkit](../01_workflow-agent-toolkit/index.md) — the tool catalogue behind `CreateToolkit`.
- [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md) — permission, budgets and dirty marking.
