# Workflow Agent — 设计模式 — 构建者

每个 `With*` 方法返回同一个可变作用域，配置可以链式书写并在多处调用点拆分。终结方法（`Provide*`、`CreateToolkit`、`ProvideTools`）把已配置的状态物化。

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 155-183 行

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
