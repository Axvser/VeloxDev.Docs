# Workflow Agent — Namespace: `VeloxDev.AI.Workflow`

Core agent-scope types: `WorkflowAgentScope` (the fluent builder), `WorkflowStateTracker` (snapshots/diffs), `WorkflowAgentContextProvider` (per-turn render), and `AgentContextCollector` (context blocks). All live in `VeloxDev.AI.Workflow`, implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/`.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/**`) + **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`).

> Entry point is `AgentEx.AsAgentScope(this IWorkflowTreeViewModel)` — see the `agentex` page.

## WorkflowAgentScope — properties

`public class WorkflowAgentScope(IWorkflowTreeViewModel tree) : IAgentToolCallNotifier`. Obtained via `tree.AsAgentScope()`. Not sealed.

| Member | Type | Notes |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel { get; }` | The scoped tree every tool operates on. |
| `MaxToolCalls` | `int? { get; private set; }` | Cumulative call cap; `null` = unlimited. |
| `AutoMarkDirty` | `bool { get; private set; }` | When `true`, every non-query call auto-marks dirty. |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | `IAgentToolCallNotifier` — raised after each call. |
| `PromptLanguage` | `AgentLanguages { get; }` | The prompt language set by `WithPromptLanguage`. |
| `Version` | `long { get; }` | Monotonic configuration version; advances on every real change. |
| `Changed` | `event EventHandler?` | Raised when `Version` advances. |
| `DisabledToolNames` | `IReadOnlyList<string> { get; }` | Tools switched off. |
| `Skills` | `SkillScope? { get; private set; }` | Attached skill subsystem (`WithSkills`). |
| `Mcp` | `McpScope? { get; private set; }` | Attached MCP subsystem (`WithMcps`). |
| `SubAgents` | `SubAgentScope? { get; private set; }` | Attached sub-agent subsystem (`WithSubAgents`). |
| `Transcript` | `AgentTranscript? { get; }` | Attached conversation (`WithTranscript`). |
| `Pipeline` | `AgentPipeline { get; }` | The composed stage chain. |
| `Todo` | `TodoProvider? { get; private set; }` | Framework todo provider (`WithTodoTracking`). |
| `AgentMode` | `AgentModeProvider? { get; private set; }` | Framework mode provider (`WithAgentModes`). |
| `CheckpointStore` | `IExecutionCheckpointStore? { get; private set; }` | Host checkpoint store (`WithCheckpointStore`). |

## WorkflowAgentScope — fluent surface

All `With*` return the same scope. Grouped by purpose.

### Language & budgets

| Member | Signature |
|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` |

### Type registration

| Member | Signature |
|---|---|
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `(Type[] …, AgentLanguages? language = null)` |
| `WithAutoDiscovery` | `WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)` |
| `WithAutoDiscovery` | `WithAutoDiscovery(string assemblyName, AgentLanguages? language = null)` |

### Custom tools

| Member | Signature |
|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` |

### Per-tool switches

| Member | Signature | Notes |
|---|---|---|
| `WithToolEnabled` | `WithToolEnabled(string toolName, bool enabled = true)` | Fluent; bumps `Version` only on a real move. |
| `SetToolEnabled` | `bool SetToolEnabled(string toolName, bool enabled)` | Runtime; returns whether the switch moved. |
| `IsToolEnabled` | `bool IsToolEnabled(string toolName)` | Reads the current state. |

### Capability gates

| Member | Signature | Notes |
|---|---|---|
| `WithAllowNodeExecution` | `WithAllowNodeExecution(bool enabled = false)` | Opt-in gate for the code-running Execution tools. |
| `WithAllowedGenericCommands` | `WithAllowedGenericCommands(params string[] commandNames)` | Allowlist for `ExecuteCommandOnNode` / `ExecuteCommandById`. |
| `WithAutoMarkDirty` | `WithAutoMarkDirty(bool enabled = false)` | Auto dirty-mark after mutations. |

### Interaction & approval

| Member | Signature |
|---|---|
| `WithInteractionSafety` | `WithInteractionSafety(int level)` |
| `WithInteractionSafetyPrompt` | `WithInteractionSafetyPrompt(int level, string promptBody)` |
| `WithSelectionHandler` | `WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` |
| `WithConfirmationHandler` | `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` |
| `WithToolApproval` | `WithToolApproval(bool enabled = true)` |

### Hosting & plumbing

| Member | Signature | Notes |
|---|---|---|
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | Marshals every tool call. |
| `WithToolCallCallback` | `WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | Async handler after every call. |
| `WithLogWriter` | `WithLogWriter(ILogWriter? writer)` | Routes a compiled run's log lines; `LogFilePath` exposes a `TextWriterLogWriter`'s path. |
| `WithCheckpointStore` | `WithCheckpointStore(IExecutionCheckpointStore? store)` | Where `ContinueCompiledWorkflow` reads from. |
| `WithSessionConfiguration` | `WithSessionConfiguration(Action<RuntimeContext> configure)` | Applied to the `RuntimeContext` of each compiled run before the run tools fill in what is unset. |
| `WithTranscript` | `WithTranscript(AgentTranscript transcript)` | Attach the conversation; throws `InvalidOperationException` if one is already attached. |
| `WithContextProvider` | `WithContextProvider(Func<WorkflowAgentScope, AIContextProvider> factory)` | Adds a host provider factory. |

### Subsystems & framework scaffolding

| Member | Signature |
|---|---|
| `WithSkills` | `WithSkills(string rootPath)` / `WithSkills(SkillScope skills)` |
| `WithMcps` | `WithMcps(McpScope mcp)` |
| `WithSubAgents` | `WithSubAgents(SubAgentScope subAgents)` |
| `WithTodoTracking` | `WithTodoTracking(TodoProviderOptions? options = null)` |
| `WithAgentModes` | `WithAgentModes(AgentModeProviderOptions options)` |
| `WithContextCompaction` | `WithContextCompaction(int maxContextWindowTokens, int maxOutputTokens)` |

### Prompts, tools & providers

| Member | Signature | Notes |
|---|---|---|
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | Compact prompt. |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `(AgentLanguages)` | Full prompt. |
| `ProvideFrameworkContext` / `ProvideCustomerContext` | `string …(AgentLanguages = English)` | Context blocks. |
| `ProvideFrameworkDataContext` / `ProvideCustomerDataContext` | `string …(AgentLanguages = English)` | Data blocks. |
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | One cached instance per scope. |
| `ProvideTools` | `IList<AITool> ProvideTools()` / `(WorkflowToolCategory)` | Tool set. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider()` | A single `WorkflowAgentContextProvider`. |
| `CreateContextProviders` | `IReadOnlyList<AIContextProvider> CreateContextProviders()` | The full fixed-order list. |
| `CreateSkillToolkit` | `SkillAgentToolkit CreateSkillToolkit()` | Throws `InvalidOperationException` if no skill scope is attached. |

### Nested `SelectionResult`

`public sealed class SelectionResult` — the low-level result the `RequestSelection` tool consumes: `SelectedOption` (`string?`), `SelectedOptions` (`IReadOnlyList<string>`), `FreeTextResponse` (`string?`), plus `static Single(string?)` / `Static Multi(IReadOnlyList<string>, string? freeText = null)` / `Static FreeText(string)`.

## WorkflowStateTracker

`public sealed class WorkflowStateTracker(IWorkflowTreeViewModel tree)` — memento-style JSON snapshot/diff so the agent tracks changes with minimal context. Constructed automatically by the toolkit; also usable standalone.

| Member | Signature | Notes |
|---|---|---|
| `Version` | `long { get; }` | Monotonically increasing snapshot version. |
| `TakeSnapshot` | `string TakeSnapshot()` | Builds the snapshot (indented JSON: `nodeCount`, `linkCount`, `nodes[]` with `index`/`id`/`type`/geometry/scalar props/`slotIds`, `links[]`), stores it as the last snapshot, increments `Version`. |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | No previous snapshot → `status = "full"` with the whole state; otherwise `status = "diff"` with `addedNodes`/`removedNodes`/`modifiedNodes` (property-level `from`/`to`), `addedLinks`/`removedLinks`, keyed by `RuntimeId`, plus previous/current counts. |

Throws `InvalidOperationException` when a component does not implement `IWorkflowIdentifiable` (no stable `RuntimeId`). The property diff compares only scalar (`string`/`int`/`double`/`bool`/`long`/`float`/`decimal`) and enum-typed properties.

## WorkflowAgentContextProvider

`public sealed class WorkflowAgentContextProvider : AIContextProvider`. **The sole source of tools and instructions per turn.** Keys its cached render on the scope's `ContextKey` (the `Version` plus a budget-usage band); on an unchanged turn it takes no lock, allocates nothing and returns the very same `AIContext` instance. Its `StateKeys` is per scope (so two providers over one scope share a key, two scopes never do).

```csharp
public WorkflowAgentContextProvider(WorkflowAgentScope scope)
public override IReadOnlyList<string> StateKeys { get; }
protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext, CancellationToken)
```

## AgentContextCollector

`public static class AgentContextCollector` — produces the human-readable context blocks embedded in the prompts. `GetAgentContext` delegates to `AgentContextReader` in Core; the `Get*Context` methods render markdown blocks used by the framework/customer providers.

| Member | Signature | Notes |
|---|---|---|
| `GetAgentContext` | `string[] GetAgentContext(Type, AgentLanguages)` / `(MemberInfo, AgentLanguages)` | `[AgentContext]` values for a type / member + language. |
| `GetEnumContext` | `string GetEnumContext(Type, AgentLanguages)` | Enum block: underlying type + member value table. |
| `GetInterfaceContext` | `string GetInterfaceContext(Type, AgentLanguages)` | Interface block; throws `ArgumentException` if `type` is not an interface. |
| `GetClassContext` | `string GetClassContext(Type, AgentLanguages)` | Class block: interfaces, developer instructions, `[VeloxProperty]`/slot-enumerator props (with `[SlotSelectors]` allowed types), `[VeloxCommand]` commands. |
| `GetDataContext` | `string GetDataContext(Type, AgentLanguages)` | Data-type block for value objects. |
