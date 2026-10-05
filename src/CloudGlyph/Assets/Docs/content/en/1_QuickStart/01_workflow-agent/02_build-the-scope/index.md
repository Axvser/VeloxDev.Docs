# 02 · Build the Agent Scope

The scope is the object that binds one workflow tree to one agent configuration. Every `With*` call returns the same scope, so the whole configuration is one chain.

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Workflow;

WorkflowAgentScope scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)     // language of the prompt / [AgentContext] docs
    .WithOutputLanguage(AgentLanguages.Chinese)     // language the model must answer in
    .WithAutoDiscovery()                            // registers the compiled context tree's customer types
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithAutoMarkDirty(false);
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

**Expected result:** `scope` constructs with no exception. Constructing the scope never touches the network or a model — it only records configuration.

## 1. The entry point

| Member | Signature | Notes |
|---|---|---|
| `AgentEx.AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | The only entry point — the scope is not usable without a tree. |

## 2. Language, discovery, budgets

| Member | Signature | Effect |
|---|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | Global default language for the prompt and `[AgentContext]` docs when a per-call `language` is `null`. Call it first; it also propagates to an already-attached `SkillScope`. |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` | Language the LLM must reply in (independent of prompt language). |
| `WithAutoDiscovery` | `WithAutoDiscovery(AgentLanguages? language = null)` | Registers every type entry under the compiled context tree's `Customer/` root — components (grouped by the four component interfaces), enums, interfaces and data. **Nothing is scanned at runtime**; see §3. |
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `(Type[] …, AgentLanguages? language = null)` | Register types explicitly instead of scanning. |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` | Cumulative tool-call cap. |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` | Separate cap on read-only (query) calls. |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` | Separate cap on mutation (non-query) calls. |

`AgentLanguages` is a `byte` enum with 33 members (`English = 0`, `ChineseSimplified = 1` with the alias `Chinese`, …, `Persian = 32`), plus `AgentLanguagesExtensions` (`ToLanguageCode`, `TryParseLanguageCode`, `ParseLanguageCode`, `GetDisplayName`).

## 3. Type discovery in detail

The context tree is built **at compile time** by walking the compilation, so `WithAutoDiscovery` is a set of directory listings rather than a runtime scan:

| Directory under `Customer/` | What it holds |
|---|---|
| `Enums` | enum types the generator admitted |
| `Interfaces` | interface types used as member types |
| `Data` | data types — `[AgentContext]`-annotated classes and structs, **and (since 2026-10-05) a plain class exposed as the declared type of a member on an already-listed type** |
| `Components/{kind}` | the four component kinds, grouped by `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` |

**What gets registered is what the generator admitted.** A type nothing annotates, no component interface reaches and no member references is not in the tree, and is not registered here either — there would be no context to render for it. Framework types live under `Framework/`, and only `Customer/` is read.

Source: `WorkflowAgentScope.cs:969-986`; the reachability rule for the data widening is `AIContextModel.cs:311-322` and `:377-399`.

**Expected result:** after `WithAutoDiscovery()`, the scope holds the compiled tree's customer registrations; asking for a type the generator never admitted yields no context block.

## 4. Prompt providers

| Member | Signature | Effect |
|---|---|---|
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | Compact system prompt. |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `(AgentLanguages)` | Full self-contained prompt. |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | Context blocks for the built-in enums/interfaces/components. |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | Context blocks for registered customer types. |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | Data blocks for `Anchor`, `Offset`, `Size`, `IAccessContext`, `ITaskContext`, `TaskContext`, `ICompileContext`, `IRuntimeContext`. |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | Data blocks for registered customer data types. |

`ProvideProgressiveContextPrompt` keeps the initial prompt small: behavioural constraints, the failure-handling protocol, built-in references, the registered-type list with one-line summaries, custom tools, the interaction-safety policy, skills and the output-language directive. Full property/command tables are **not** preloaded — the model is told to call `GetComponentContext` with a full type name before operating on a type.

```csharp
var skeleton = scope.ProvideProgressiveContextPrompt();   // static skeleton — freeze into ChatOptions.Instructions
var providers = scope.CreateContextProviders();           // per-turn: envelope + skills + MCP + sub-agents + framework
```

**Expected result:** `skeleton` is a non-empty markdown string containing the "Interaction Safety Policy" section; `providers` contains at least one `WorkflowAgentContextProvider`.

## 5. Tool production

| Member | Signature | Effect |
|---|---|---|
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | The toolkit over this scope (one cached instance per scope). |
| `ProvideTools` | `IList<AITool> ProvideTools()` | All tools, honoring per-tool switches. |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | Restricted to the given category flags. |

Custom tools registered via `WithTools` / `WithQueryTools` are always included, whatever the category flags. See the Tool Budgets page for what happens when a tool is switched off.

**Expected result:** `scope.ProvideTools().Count` is `69` for a scope with node execution enabled and both interaction handlers registered — the 68 built-in tools plus the always-added `ResetToolCallLimit` (see page 06 for the exact per-category breakdown). The `Execution` and `Command` gates are checked inside each tool body, so they do not remove tools from the count; with no interaction handlers it is lower by the `Interaction` tools alone.

## Run declaration

- ⚠️ Not actually run — statically verified only. Signatures and the two-pass discovery behaviour are read from `WorkflowAgentScope.cs` and `AgentHelper.cs`; no scope was constructed from this page.
