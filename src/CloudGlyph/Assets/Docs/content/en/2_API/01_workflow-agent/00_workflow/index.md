# Workflow Agent — Namespace: `VeloxDev.AI.Workflow`

Core agent-scope types. The host builds a `WorkflowAgentScope` on a live `IWorkflowTreeViewModel`, configures it fluently, and passes the produced tools/context to an AI chat client. All types below live in `VeloxDev.AI.Workflow` and are implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/` (scope/tracker) and `Agent/Workflow/AgentContextCollector.cs`.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*`) + **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`).

> Entry point is the `AgentEx.AsAgentScope(this IWorkflowTreeViewModel)` extension — see [agentex](../04_agentex/index.md).

## WorkflowAgentScope

`public class WorkflowAgentScope(IWorkflowTreeViewModel tree) : IAgentToolCallNotifier`. Obtained via `tree.AsAgentScope()`. Binds one tree, holds the configuration state, exposes context prompts and tool production, and raises the `ToolCalled` notifier after each tool call. Not sealed — usable directly or as a base.

| Member | Type / Signature | Notes |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel { get; }` | The scoped tree every tool operates on. |
| `MaxToolCalls` | `int? { get; private set; }` | Cumulative tool-call cap; `null` = unlimited. |
| `AutoMarkDirty` | `bool { get; private set; }` | When `true`, every non-query tool call auto-marks the tree dirty. |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | `IAgentToolCallNotifier` — raised after each tool call (also feeds `WithToolCallCallback`). |

**Fluent configuration — all return the same scope for chaining.** The canonical chain (demo `AgentHelper.ProvideAgent`, lines 155–206):

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithOutputLanguage(AgentLanguages.Chinese)
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAutoMarkDirty(false)
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithToolCallCallback(args => { helper.ToolCalled?.Invoke(); return Task.CompletedTask; })
    .WithSelectionHandler(args => helper.SelectionHandler is not null ? helper.SelectionHandler(args) : Task.CompletedTask)
    .WithConfirmationHandler(args => helper.ConfirmationHandler is not null ? helper.ConfirmationHandler(args) : Task.CompletedTask);
scope.WithInteractionSafety(helper.InteractionSafety);
scope.WithTools(
    "Manage MCP servers: ListMcpServers, LoadMcpServers, UnloadMcpServer, DescribeMcpServer.",
    [.. new McpAgentToolkit(helper.Mcp, helper.McpServers).CreateTools()]);
var contextPrompt = scope.ProvideProgressiveContextPrompt();
helper.SetBaseTools(scope.ProvideTools());
```

### Language and budget

| Member | Signature | Effect |
|---|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | Global default language for prompts/`[AgentContext]` docs when a per-call `language` is `null`. Call first in the chain. |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` | Language the LLM must use for all replies (independent of prompt language). Emits the "Output Language" directive. |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` | Cumulative tool-call cap. |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` | Separate cap on read-only (query) tool calls. |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` | Separate cap on mutation (non-query) tool calls. |

### Type registration and auto-discovery

| Member | Signature | Effect |
|---|---|---|
| `WithEnums` | `WithEnums(Type[] enums, AgentLanguages? language = null)` | Register enum types for the customer context. |
| `WithInterfaces` | `WithInterfaces(Type[] interfaces, AgentLanguages? language = null)` | Register interface types. |
| `WithComponents` | `WithComponents(Type[] components, AgentLanguages? language = null)` | Register concrete workflow component classes. |
| `WithData` | `WithData(Type[] dataTypes, AgentLanguages? language = null)` | Register value-object/data types (rendered as plain data, not interactive components). |
| `WithAutoDiscovery` | `WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)` | Two-pass assembly scan (below). |
| `WithAutoDiscovery` | `WithAutoDiscovery(string assemblyName, AgentLanguages? language = null)` | Same by simple assembly name; throws `ArgumentException` if the assembly is not loaded in the current `AppDomain`. |

**`WithAutoDiscovery` two passes.** Pass 1 registers concrete workflow components (classes implementing `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel`), `[AgentContext]`-annotated enums and data classes/structs. Pass 2 deep-scans every registered component's public properties + non-public fields (backing fields) + methods to infer, per language: enum types via `[SlotSelectors]` and member types, interface types used as member types, `[AgentCommandParameter]` parameter types, and non-primitive value-object structs. Already-registered and framework-built-in types (namespaces `System*`, `Microsoft*`, `VeloxDev.WorkflowSystem`, `VeloxDev.MVVM`, `VeloxDev.Core.WorkflowSystem`, plus `FrameworkEnums`/`FrameworkInterfaces`/`FrameworkComponents`/`FrameworkData`) are never re-added. `ArgumentNullException` when `assembly` is null.

### Custom tools and UI marshalling

| Member | Signature | Effect |
|---|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` | Registers mutation-capable custom tools (always included in `ProvideTools`). Optional `promptContext` text is injected as a "Custom Tools" section. |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` | Registers read-only custom tools — never auto-marked dirty, even with `WithAutoMarkDirty(true)`. |
| `WithAutoMarkDirty` | `WithAutoMarkDirty(bool enabled = false)` | `true` = framework marks dirty after every mutation tool call. Default `false` (the prompt instructs the Agent to call `MarkDirty` once at the end). |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | Marshals every tool call onto the given context (e.g. `SynchronizationContext.Current`). Workflow components are UI-bound, so mutations must run on the owning thread. |
| `WithToolCallCallback` | `WithToolCallCallback(Func<AgentToolCallEventArgs, Task> handler)` | Async handler invoked after every tool call; replaces any previous handler. |

Note: `WithTools`/`WithQueryTools` `AIFunction` tools are wrapped with the same tracked wrapper (UI marshal, call counting, callback, auto-dirty); non-`AIFunction` tools (e.g. raw MCP client tools) are added as-is.

### Capability gates — enforced in code, not prompt prose

| Member | Signature | Effect |
|---|---|---|
| `WithAllowNodeExecution` | `WithAllowNodeExecution(bool enabled = false)` | Opt-in gate for the Execution tools that run arbitrary node business code: `ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`. Default denied. |
| `WithAllowedGenericCommands` | `WithAllowedGenericCommands(params string[] commandNames)` | Allowlists command names for `ExecuteCommandOnNode` / `ExecuteCommandById`; the `"Command"` suffix is optional. Never called → generic command execution is disabled entirely (secure default). |

### Interaction safety and handlers

| Member | Signature | Effect |
|---|---|---|
| `WithInteractionSafety` | `WithInteractionSafety(int level)` | 0 silent, 1 cautious (default), 2 balanced, 3 strict; values outside 0–3 are clamped. |
| `WithInteractionSafetyPrompt` | `WithInteractionSafetyPrompt(int level, string promptBody)` | Replaces the "Interaction Safety Policy" body text for a level (1–3); level 0 always uses the built-in silent rule and cannot be overridden. |
| `WithSelectionHandler` | `WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` | Registers the `RequestSelection` handler; `null` removes the tool. The handler must set `SelectedOption` (single) / `SelectedOptions` (multi) and/or `FreeTextResponse`. |
| `WithConfirmationHandler` | `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` | Registers the `RequestConfirmation` handler; `null` removes the tool. The handler must set `Result`. |

**Semantics.** Level 0 registers no interaction tools and emits no policy. Levels 1–3 emit an "Interaction Safety Policy" built from embedded `Safety/Shared.md` + `Safety/Level{n}.md`, plus any host override. `AllowAlways` confirmations are remembered per `operationKey` for the session (`ResolveConfirmationAsync`).

### Context prompts

| Member | Signature | Effect |
|---|---|---|
| `ProvideAllContexts` | `string ProvideAllContexts()` / `ProvideAllContexts(AgentLanguages)` | Full context: built-in references, framework context, framework data types, customer context, customer data types, failure-handling protocol, custom tools, interaction-safety policy, skills, output-language directive. |
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `ProvideProgressiveContextPrompt(AgentLanguages)` | Compact progressive system prompt (see below). |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | Context blocks for built-in enums (`SlotChannel`, `SlotState`, `RouterCompileMode`), interfaces and components. |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | Context blocks for registered customer enums/interfaces/components. |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | Data-type context for `Anchor`, `Offset`, `Size`, `IAccessContext`, `ITaskContext`, `TaskContext`, `ICompileContext`, `IRuntimeContext`. |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | Data-type context for registered customer data types. |

**`ProvideProgressiveContextPrompt`** keeps the initial prompt small: critical behavioral constraints, the failure-handling protocol, built-in references, the registered-type list with one-line summaries, custom tools, interaction-safety policy, skills and the output-language directive. Full property/command tables are intentionally **not** preloaded — the Agent is instructed to call `GetComponentContext` with the full type name before operating on a type.

### Tool production

| Member | Signature | Effect |
|---|---|---|
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | Builds a `WorkflowAgentToolkit` over this scope (each instance owns a `WorkflowStateTracker`). |
| `ProvideTools` | `IList<AITool> ProvideTools()` | `CreateToolkit().CreateTools()` — all tools. |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | Tools restricted to the given category flags; custom tools registered via `WithTools`/`WithQueryTools` are always included. |

### `WorkflowAgentScope.SelectionResult` (nested)

`public sealed class SelectionResult` — the low-level result consumed by `WorkflowAgentToolkit.RequestSelection`.

| Member | Type | Notes |
|---|---|---|
| `SelectedOption` | `string?` | Single-select: the chosen option; `null` if cancelled. |
| `SelectedOptions` | `IReadOnlyList<string>` | Multi-select: chosen options (empty if none). |
| `FreeTextResponse` | `string?` | Free-text answer; `null`/empty if not provided. |
| `Single(string? option)` | static | Creates a single-select result. |
| `Multi(IReadOnlyList<string> options, string? freeText = null)` | static | Creates a multi-select result. |
| `FreeText(string text)` | static | Creates a free-text-only result. |

## WorkflowStateTracker

`public sealed class WorkflowStateTracker(IWorkflowTreeViewModel tree)`. Memento-style JSON snapshot/diff helper so the Agent tracks changes with minimal context. Constructed automatically by the toolkit; also usable standalone.

| Member | Signature | Notes |
|---|---|---|
| `Version` | `long { get; }` | Monotonically increasing snapshot version. |
| `TakeSnapshot` | `string TakeSnapshot()` | Builds the state snapshot (indented JSON: `nodeCount`, `linkCount`, `nodes[]` with `index`/`id`/`type`/geometry/scalar props/`slotIds`, `links[]`), stores it as the last snapshot and increments `Version`. |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | No previous snapshot → `status = "full"` with the whole state. Otherwise `status = "diff"` with `addedNodes`/`removedNodes`/`modifiedNodes` (property-level `from`/`to`), `addedLinks`/`removedLinks`, keyed by `RuntimeId`, plus previous/current node and link counts. |

Throws `InvalidOperationException` when a component does not implement `IWorkflowIdentifiable` (no stable `RuntimeId`). The property diff compares only scalar (`string`/`int`/`double`/`bool`/`long`/`float`/`decimal`) and enum-typed properties.

## AgentContextCollector

`public static class AgentContextCollector`. Produces the human-readable context blocks embedded in the prompts. `GetAgentContext` delegates to `AgentContextReader` in Core; the `Get*Context` methods render markdown blocks used by the framework/customer providers above.

| Member | Signature | Notes |
|---|---|---|
| `GetAgentContext` | `string[] GetAgentContext(Type, AgentLanguages)` | `[AgentContext]` values for a type + language. |
| `GetAgentContext` | `string[] GetAgentContext(MemberInfo, AgentLanguages)` | `[AgentContext]` values for a member (field/property/method) + language. |
| `GetEnumContext` | `string GetEnumContext(Type, AgentLanguages)` | Enum block: underlying type + member value table. |
| `GetInterfaceContext` | `string GetInterfaceContext(Type, AgentLanguages)` | Interface block: base interfaces, non-command properties, `ICommand` properties. Throws `ArgumentException` if `type` is not an interface. |
| `GetClassContext` | `string GetClassContext(Type, AgentLanguages)` | Class block: interfaces, developer instructions, `[VeloxProperty]`/slot-enumerator properties (with `[SlotSelectors]` allowed types), `[VeloxCommand]` commands. |
| `GetDataContext` | `string GetDataContext(Type, AgentLanguages)` | Data-type block for value objects: annotated fields + public properties only (no commands/slots). |
