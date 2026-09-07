# Workflow Agent — Design Patterns — Builder

`WorkflowAgentScope` is a mutable, fluent builder: every `With*` method mutates the same instance and returns `this`, so configuration can be chained and split across call sites. The terminal methods (`Provide*`, `CreateToolkit`, `ProvideTools`) materialize the configured state — the built-in prompt is assembled by `ProvideProgressiveContextPrompt()` / `ProvideAllContexts()` and the tool list by `ProvideTools()`.

The demo wires the full builder chain in one place (`AgentHelper.ProvideAgent`):

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 155-183

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)   // default prompt language
    .WithOutputLanguage(AgentLanguages.Chinese)   // default output language
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAutoMarkDirty(false)               // whether the view auto-marks itself dirty
    .WithMaxToolCalls(200)                  // maximum tool call count
    .WithAllowNodeExecution(true)           // explicitly allow the Agent to run node business code (safely off by default; the demo needs it)
    .WithSynchronizationContext(SynchronizationContext.Current) // marshal tool calls to the UI thread (components are UI-bound)
    .WithToolCallCallback(args =>           // tool-call callback
    {
        helper.ToolCalled?.Invoke();
        return Task.CompletedTask;
    })
    .WithSelectionHandler(async args => // the Agent asks the user which action to perform
    {
        if (helper.SelectionHandler is not null)
            await helper.SelectionHandler(args);
    })
    .WithConfirmationHandler(async args => // the Agent asks the user to confirm operation permissions
    {
        if (helper.ConfirmationHandler is not null)
            await helper.ConfirmationHandler(args);
    });

// Interaction-tool aggressiveness 0~3
scope.WithInteractionSafety(helper.InteractionSafety);
```

Because the terminal methods read the accumulated state, several `With*` calls may be split across methods (e.g. `WithInteractionSafety` + per-level `WithInteractionSafetyPrompt` are applied after the chain), and the same scope is then used to produce both the system prompt and the tool list, guaranteeing the two stay consistent.

> Source of the `With*` implementation: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`, lines 106-283.
