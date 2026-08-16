# Workflow Agent — Design Patterns — Builder

Every `With*` method returns the same mutable scope, so configuration can be chained and split across call sites. The terminal methods (`Provide*`, `CreateToolkit`, `ProvideTools`) materialize the configured state.

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 155-183

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithOutputLanguage(AgentLanguages.Chinese)
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithToolCallCallback(args => { helper.ToolCalled?.Invoke(); return Task.CompletedTask; })
    .WithSelectionHandler(async args => { if (helper.SelectionHandler is not null) await helper.SelectionHandler(args); })
    .WithConfirmationHandler(async args => { if (helper.ConfirmationHandler is not null) await helper.ConfirmationHandler(args); });
scope.WithInteractionSafety(helper.InteractionSafety);
```
