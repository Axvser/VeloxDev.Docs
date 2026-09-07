# Workflow Agent — Build the Agent Scope

`WorkflowAgentScope` is the fluent configuration object that turns a tree into an agent-controllable surface. Everything the agent may inspect, touch or run is decided here: languages, type discovery, budgets, gates, handlers and custom tools.

## 1. Create the scope

`tree.AsAgentScope()` (extension declared in `VeloxDev.AI.Workflow`, file `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`) returns a fresh builder. Start with the languages and auto-discovery:

```csharp
var scope = tree.AsAgentScope()                  // tree: IWorkflowTreeViewModel
    .WithPromptLanguage(AgentLanguages.English)  // default language for prompts & docs
    .WithOutputLanguage(AgentLanguages.Chinese)  // language the LLM must reply in
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib");
```

- `WithPromptLanguage(language)` sets the language used for every built-in prompt/document section. It has a global default (`English`); call it first, before other registrations that derive from it.
- `WithOutputLanguage(language)` emits an "Output Language" directive the model must follow when replying. It is independent of the prompt-document language — you can document in English and demand Chinese replies, as the demo does.
- `WithAutoDiscovery(Assembly)` / `WithAutoDiscovery(assemblyName)` scans one assembly in two passes: it registers concrete workflow component classes, `[AgentContext]`-annotated enums and data classes, then deep-scans the registered components' properties/fields/methods to infer referenced enums, interfaces and data (via `[SlotSelectors]`, `[AgentCommandParameter]`, member and generic types). Framework built-ins are never re-added. The string overload resolves the assembly by simple name from the current `AppDomain`.

If you prefer explicit control, register exactly what you need per language with `WithEnums(Type[], AgentLanguages?)`, `WithInterfaces(Type[], ...)`, `WithComponents(Type[], ...)` and `WithData(Type[], ...)` — auto-discovery is just sugar over these four.

**Expected result:** `scope` builds without exception; its `Tree` property equals `tree`.

## 2. Produce the system prompt (bilingual docs are read automatically)

The scope offers two prompt providers; both embed the prompt documents shipped under `Src/Core/VeloxDev.Core.Extension/Resources/Workflow/{en,zh}` (`References/`, `Skills/`, `Safety/`), selected by the current prompt language with English fallback:

```csharp
var progressive = scope.ProvideProgressiveContextPrompt();   // small, lazy
var allContexts = scope.ProvideAllContexts();                // full, self-contained
```

- **Progressive** (`ProvideProgressiveContextPrompt()`) — hardcoded behavioral constraints, the failure-handling protocol, all `References`, then a compact **type registry** (framework interfaces/bases/data plus every registered customer enum/interface/component/data full name) with **one-line** summaries pulled from `[AgentContext]`. It tells the model to fetch the full property/command tables on demand with `GetComponentContext` / `GetWorkflowSummary` / `ListComponentCommands`. Low initial token cost.
- **All contexts** (`ProvideAllContexts()`) — the same content but with the whole framework and customer **tables inlined** (no lazy fetch). Self-contained, high token cost.

Whichever you choose, the embedded docs teach the agent the rules it must follow — e.g. the `Skills/CompilerUsage.md` (three execution entries, Root vs Terminal, routers are never bypassed), `Skills/OperationOrdering.md` (mandatory create → patch → connect → execute ordering), `References/CommandReference.md` (command-first mutation rule), `References/CoordinateSystem.md` (canvas coordinates), plus the `Safety/` level policies.

**Expected result:** both calls return a non-empty string; the progressive prompt's type-registry section lists your discovered types by full name with their `[AgentContext]` summaries.

## 3. Fetch the tool set

```csharp
var toolkit = scope.CreateToolkit();                         // WorkflowAgentToolkit
var allTools = scope.ProvideTools();                         // IList<AITool>, all categories
var queryOnly = scope.ProvideTools(WorkflowToolCategory.Query); // filtered surface
```

- `CreateToolkit()` returns the `WorkflowAgentToolkit` (namespace `VeloxDev.AI.Workflow.Functions`) that holds the tree tracker and per-call counters.
- `ProvideTools()` returns every built-in tool (60 by default; up to 62 when interaction safety is on and handlers are registered) **plus** any custom tools you registered later with `WithTools` / `WithQueryTools`.
- `ProvideTools(WorkflowToolCategory)` returns only the requested category — e.g. `Query` gives you the read-only inspection and compile-plan tools with no mutation surface.

`WorkflowToolCategory` and `WorkflowAgentToolkit` live in namespace `VeloxDev.AI.Workflow.Functions` — add `using VeloxDev.AI.Workflow.Functions;` when you reference the category enum or the toolkit type explicitly (calling `ProvideTools()` on its own needs no such using, since it returns `IList<AITool>`).

**Expected result:** `ProvideTools()` is a non-empty `IList<AITool>`; `ProvideTools(WorkflowToolCategory.Query)` contains no mutation, execution or command tools.

## Run declaration

- ⚠️ Statically verified only — signatures verified against `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs` and `AgentEx.cs`; the sample was not compiled or executed.
