# Workflow Agent — 设计模式 — 构建者

`WorkflowAgentScope` 是一个可变、流畅的构建者：每个 `With*` 方法修改同一个实例并返回 `this`，因此配置可以链式书写并在多处调用点拆分。终结方法（`Provide*`、`CreateToolkit`、`ProvideTools`）把已配置的状态物化——内置提示词由 `ProvideProgressiveContextPrompt()` / `ProvideAllContexts()` 组装，工具列表由 `ProvideTools()` 生成。

Demo 把完整构建链写在一处（`AgentHelper.ProvideAgent`）：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 155-183 行

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

因为终结方法读取累加的状态，多个 `With*` 调用可以跨方法拆分（例如链式完成后补调 `WithInteractionSafety` 与逐级 `WithInteractionSafetyPrompt`），且同一个 scope 既用于生成系统提示词又用于生成工具列表，保证两者保持一致。

> `With*` 的实现源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`，第 106-283 行。
