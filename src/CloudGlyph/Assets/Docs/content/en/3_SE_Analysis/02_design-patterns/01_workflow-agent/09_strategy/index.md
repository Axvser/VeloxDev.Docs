# Workflow Agent — Design Patterns — Strategy

Two strategy seams let the host choose *how* the agent behaves without changing the toolkit:

**1. Tool-surface selection.** `WorkflowToolCategory` is a `[Flags]` enum (`Query`, `Mutation`, `Execution`, `Command`, `Graph`, `Layout`, `Analytics`, `State`, `Composite`, `Interaction`). `CreateTools(categories)` registers only the selected groups, which lowers per-request token cost and improves tool-selection accuracy. `Query` is read-only; `Execution`/`Command` groups carry the capability-gated tools; `Interaction` is registered only when a handler exists **and** safety level > 0.

> Source: `WorkflowToolCategory.cs`; `WorkflowAgentToolkit.cs`, lines 145-152

```csharp
if (_scope.IsInteractionAllowed)
{
    if (_scope.SelectionHandler != null)
        Add(WorkflowToolCategory.Interaction, T(RequestSelection, nameof(RequestSelection)));
    if (_scope.ConfirmationHandler != null)
        Add(WorkflowToolCategory.Interaction, T(RequestConfirmation, nameof(RequestConfirmation)));
}
```

**2. Interaction strategy.** `WithSelectionHandler` / `WithConfirmationHandler` inject the host's interactive-response strategy behind the `RequestSelection` / `RequestConfirmation` tools, and `WithInteractionSafety(0-3)` selects how eagerly those tools are used (`0` = fully autonomous, never interact; `3` = ask before every non-trivial mutation). `ResolveConfirmationAsync` remembers `AllowAlways` decisions per `operationKey` for the session, so the chosen policy is enforced by code, not just prompt text (`WorkflowAgentScope.cs`, lines 324-442).

The demo sets the interaction strategy per-host via `AgentHelper.InteractionSafety` (default 3) and optional per-level prompt overrides (`AgentHelper.InteractionSafetyPrompts`) — `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 139-150.
