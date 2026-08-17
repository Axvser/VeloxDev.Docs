# Workflow Agent — Namespace: `VeloxDev.AI.Workflow`

### `WorkflowAgentScope`

Fluent builder obtained via `tree.AsAgentScope()`. Implements `IAgentToolCallNotifier`. Holds the scoped tree (`Tree`), `MaxToolCalls`, `AutoMarkDirty`, and the `ToolCalled` event.

#### `AsAgentScope` (entry point)

**Signature:** `public static WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` — see `AgentEx`.
**Returns:** a new `WorkflowAgentScope` bound to `tree`.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, line 155.
**Notes:** this is the only entry point; the scope is not usable without a tree.

#### Fluent configuration — full surface

| Member | Signature | Effect |
|---|---|---|
| `WithPromptLanguage` | `WorkflowAgentScope WithPromptLanguage(AgentLanguages)` | Default language for prompts/docs; call first in the chain. |
| `WithOutputLanguage` | `WorkflowAgentScope WithOutputLanguage(AgentLanguages)` | Language the LLM must use for replies (independent of prompt language). |
| `WithMaxToolCalls` | `WorkflowAgentScope WithMaxToolCalls(int)` | Cumulative tool-call cap. |
| `WithMaxReadToolCalls` | `WorkflowAgentScope WithMaxReadToolCalls(int)` | Separate cap on read-only (query) tool calls. |
| `WithMaxWriteToolCalls` | `WorkflowAgentScope WithMaxWriteToolCalls(int)` | Separate cap on mutation tool calls. |
| `WithAutoMarkDirty` | `WorkflowAgentScope WithAutoMarkDirty(bool enabled = false)` | Auto-`MarkDirty` on every non-query tool call. Default `false` (the prompt then instructs the Agent to call `MarkDirty` once). |
| `WithAllowNodeExecution` | `WorkflowAgentScope WithAllowNodeExecution(bool enabled = false)` | Opt-in gate for `ExecuteNode`/`ExecuteNodes`/`BroadcastNode`/`ReverseBroadcastNode`/`RunCompiledWorkflow`. Default denied. |
| `WithAllowedGenericCommands` | `WorkflowAgentScope WithAllowedGenericCommands(params string[])` | Allowlists command names for `ExecuteCommandOnNode`/`ExecuteCommandById`; `"Command"` suffix optional. Never called → generic execution disabled. |
| `WithSynchronizationContext` | `WorkflowAgentScope WithSynchronizationContext(SynchronizationContext?)` | Marshals every tool call onto the UI thread. Pass `SynchronizationContext.Current` during setup. |
| `WithToolCallCallback` | `WorkflowAgentScope WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` | Async handler invoked after every tool call. Replaces any previous handler. |
| `WithSelectionHandler` | `WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` | Registers the `RequestSelection` handler; `null` removes the tool. |
| `WithConfirmationHandler` | `WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` | Registers the `RequestConfirmation` handler; `null` removes the tool. |
| `WithInteractionSafety` | `WorkflowAgentScope WithInteractionSafety(int level)` | 0 silent, 1 cautious, 2 balanced, 3 strict; clamped to 0–3. |
| `WithInteractionSafetyPrompt` | `WorkflowAgentScope WithInteractionSafetyPrompt(int level, string promptBody)` | Overrides the prompt body for a level (1–3); level 0 cannot be overridden. |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(Assembly, AgentLanguages? = null)` | Scans an assembly and registers components/enums/interfaces/data (two passes, deduplicated). |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(string assemblyName, AgentLanguages? = null)` | Same by simple assembly name; throws `ArgumentException` if not found in the current `AppDomain`. |
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `WorkflowAgentScope With*(Type[], AgentLanguages? = null)` | Manual type registration per language bucket. |
| `WithTools` | `WorkflowAgentScope WithTools(string? promptContext, params AITool[])` | Merge mutation-capable custom tools + optional prompt text. |
| `WithQueryTools` | `WorkflowAgentScope WithQueryTools(string? promptContext, params AITool[])` | Merge read-only custom tools (never auto-marked dirty). |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `string ProvideAllContexts(AgentLanguages)` | Full context string (framework + customer contexts, failure protocol, safety policy, skills). |
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | Compact progressive system prompt. |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | Context for built-in framework enums/interfaces/components. |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | Context for registered customer enums/interfaces/components. |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | Data context for framework value types (`Anchor`, `Offset`, `Size`, `IAccessContext`, `ITaskContext`, `TaskContext`, `ICompileContext`, `IRuntimeContext`). |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | Data context for registered customer data types. |
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | Builds a `WorkflowAgentToolkit` over this scope. |
| `ProvideTools` | `IList<AITool> ProvideTools()` | `CreateToolkit().CreateTools()` — all tools. |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory)` | Tools restricted to the given category flags; custom tools always included. |

#### `WorkflowAgentScope.WithAutoDiscovery` (two-pass scan)

**Signature:** `public WorkflowAgentScope WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)`
**Returns:** the same scope, for chaining.
**Exceptions:** `ArgumentNullException` when `assembly` is null; `ArgumentException` for the string overload when the assembly name is not loaded.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 159–160.
**Notes:** Pass 1 registers concrete workflow components, `[AgentContext]`-annotated enums and data types; Pass 2 deep-scans every registered component's properties/fields/methods to infer enums (via `[SlotSelectors]`), interfaces, `[AgentCommandParameter]` parameter types, and non-primitive value objects. Already-registered and framework-builtin types are never re-added. *Complexity is analyzed on the SE complexity page.*

#### `WorkflowAgentScope.ProvideProgressiveContextPrompt`

**Signature:** `public string ProvideProgressiveContextPrompt()` / `public string ProvideProgressiveContextPrompt(AgentLanguages language)`
**Returns:** the compact system prompt: critical behavioral constraints, failure-handling protocol, built-in references, registered-type list with one-line summaries, custom-tools section, interaction-safety policy, skills, and the output-language directive.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, line 200.
**Notes:** Progressive disclosure — the full property/command tables are intentionally not preloaded; the Agent is instructed to call `GetComponentContext` before operating on a type.

#### `WorkflowAgentScope.WithSelectionHandler` / `WithConfirmationHandler`

**Signature:** `public WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` and `public WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)`
**Returns:** the same scope.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 170–179; host dialogs in `Examples/Workflow/WinForms/Demo/Form1.cs` (`ShowSelectionDialogAsync`, `ShowConfirmationDialogAsync`).
**Notes:** the handler is null → the corresponding tool is not registered. The selection handler must set `SelectedOption`/`SelectedOptions`/`FreeTextResponse`; the confirmation handler must set `Result`. `AllowAlways` approvals are remembered per `operationKey` for the session.

#### `WorkflowAgentScope.WithInteractionSafety`

**Signature:** `public WorkflowAgentScope WithInteractionSafety(int level)`
**Returns:** the same scope.
**Exceptions:** none (values outside 0–3 are clamped).
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, line 182.
**Notes:** level 0 registers no interaction tools and emits no safety policy; levels 1–3 emit an "Interaction Safety Policy" built from embedded `Safety/Shared.md` + `Safety/Level{n}.md` plus any `WithInteractionSafetyPrompt` override.

#### `WorkflowAgentScope.CreateToolkit` / `ProvideTools`

**Signature:** `public WorkflowAgentToolkit CreateToolkit()` and `public IList<AITool> ProvideTools()` / `public IList<AITool> ProvideTools(WorkflowToolCategory categories)`
**Returns:** the toolkit / a list of `AITool`.
**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 197–204.
**Notes:** every built-in tool is wrapped in a `TrackedAIFunction` (UI-thread marshal, call counting, max-call enforcement, `ToolCalled` callback, optional auto-dirty). Custom `AIFunction` tools registered via `WithTools`/`WithQueryTools` are wrapped the same way; non-`AIFunction` tools (raw MCP tools) are added as-is.

### `WorkflowStateTracker`

Memento-style JSON snapshot/diff helper. Constructed by the toolkit (`new WorkflowStateTracker(scope.Tree)`); also usable standalone.

#### `TakeSnapshot`

**Signature:** `public string TakeSnapshot()`
**Returns:** the current tree state as an indented JSON string (`nodeCount`, `linkCount`, `nodes[]` with index/id/type/geometry/scalar props/slotIds, `links[]`), and stores it as the last snapshot.
**Exceptions:** `InvalidOperationException` if a component does not implement `IWorkflowIdentifiable` (no stable `RuntimeId`).
**Example:** `WorkflowAgentToolkit.cs`, tool `TakeSnapshot`.
**Notes:** `Version` increments on every snapshot.

#### `GetChangesSinceLastSnapshot`

**Signature:** `public string GetChangesSinceLastSnapshot()`
**Returns:** if no previous snapshot exists, a `status = "full"` object with the whole state; otherwise a `status = "diff"` object with `addedNodes`/`removedNodes`/`modifiedNodes` (property-level `from`/`to`) and `addedLinks`/`removedLinks`, keyed by `RuntimeId`, plus `previous/current` node and link counts.
**Example:** `WorkflowAgentToolkit.cs`, tool `GetChangesSinceSnapshot`.
**Notes:** property diff only compares scalar + enum-typed properties (string/int/double/bool/long/float/decimal/enum).
