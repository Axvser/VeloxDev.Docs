# Workflow Agent — Design Patterns — Facade

`CreateTools()` builds every tool with the local `T(...)` helper that wraps `AIFunctionFactory.Create(method, name)` in a `TrackedAIFunction`. Group registration is driven by `WorkflowToolCategory` flags.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, lines 39-161

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
