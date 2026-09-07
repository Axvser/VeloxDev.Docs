# Workflow Agent — Design Patterns — Facade

`WorkflowAgentToolkit` is the facade for the workflow-agent feature. One `CreateTools()` call registers all ~60 `AITool`s for a scoped tree, hiding type resolution, reflection-based command invocation, JSON serialization and completion-waiting behind a single surface the LLM sees as flat tool names.

`CreateTools` wraps every tool body with a local `T(...)` helper and groups the registrations by `WorkflowToolCategory` flags so the host can shrink the exposed surface:

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, lines 39-164

```csharp
AITool T(Delegate method, string name)
    => new TrackedAIFunction(AIFunctionFactory.Create(method, name), this);

var tools = new List<AITool>();
void Add(WorkflowToolCategory category, params AITool[] items)
{
    if ((categories & category) == category)
        tools.AddRange(items);
}
```

Each category block registers its tools, for example the query block begins `Add(WorkflowToolCategory.Query, T(ListNodes, nameof(ListNodes)), T(GetNodeDetail, nameof(GetNodeDetail)), ... )` — the full list runs from `ListNodes` to `GetExecutionLog`.

The facade is the single public entry an agent host uses: `scope.ProvideTools()` → `CreateToolkit().CreateTools()`. Developer-registered custom tools (via `WithTools` / `WithQueryTools`) are merged in at the end and, when they are `AIFunction`s, wrapped with the same `TrackedAIFunction` decorator; raw MCP client tools are appended as-is (`WorkflowAgentToolkit.cs`, lines 154-164).
