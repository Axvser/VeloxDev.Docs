# Workflow Agent — Design Patterns — Strategy

Two strategy seams let the host choose *how* the agent behaves without changing the toolkit:

**1. Tool-surface selection.** `WorkflowToolCategory` is a `[Flags]` enum (`Query`, `Mutation`, `Execution`, `Command`, `Graph`, `Layout`, `Analytics`, `State`, `Composite`, `Interaction`). `CreateTools(categories)` registers only the selected groups, which lowers per-request token cost and improves tool-selection accuracy. `Query` is read-only; `Execution`/`Command` groups carry the capability-gated tools; `Interaction` is registered when the matching handler exists (there is no safety-level gate).

> Source: `WorkflowToolCategory.cs`; `WorkflowAgentToolkit.CreateAllTools`

```csharp
if (_scope.SelectionHandler != null)
    Add(WorkflowToolCategory.Interaction, T(RequestSelection, nameof(RequestSelection), AgentActionCategory.Interact));
if (_scope.ConfirmationHandler != null)
    Add(WorkflowToolCategory.Interaction, T(RequestConfirmation, nameof(RequestConfirmation), AgentActionCategory.Interact));
```

**2. Permission strategy.** `WithPermissionMode(AgentPermissionMode)` selects the coarse decision matrix (`Plan`, `Manual`, `AutoEdit`, `Auto`, `Bypass`); `WithPermissionRule(decision, patterns)` adds the fine layer, and `WithPermissionJudge` supplies the `Auto`-mode decision for calls no rule settles. The policy is evaluated per call in `ToolPipeline.Confirm` and in `CheckInvocation`, so the strategy is enforced by code, not prompt text. `WithSelectionHandler` / `WithConfirmationHandler` inject the host's interactive-response behaviour behind `RequestSelection` / `RequestConfirmation`, while `ResolveConfirmationAsync` remembers `AllowAlways` decisions per `operationKey` for the session.

The demo sets the strategy per host: `AgentHelper.PermissionMode` (default `AutoEdit`) and `AgentHelper.PermissionRules` (`Ask` rules for destructive mutations), applied with `WithPermissionMode` / `WithPermissionRule` in `AgentHelper.ProvideAgent`.
