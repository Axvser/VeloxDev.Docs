# Workflow Agent — 设计模式 — 策略

两个策略接缝让宿主在不改工具包的前提下选择 Agent *如何*行动：

**1. 工具表面选择。** `WorkflowToolCategory` 是 `[Flags]` 枚举（`Query`、`Mutation`、`Execution`、`Command`、`Graph`、`Layout`、`Analytics`、`State`、`Composite`、`Interaction`）。`CreateTools(categories)` 只注册所选组，降低每次请求的 token 成本并提升工具选择准确率。`Query` 只读；`Execution`/`Command` 组携带能力门控工具；`Interaction` 仅在存在处理器**且**安全级别 > 0 时注册。

> 源码：`WorkflowToolCategory.cs`；`WorkflowAgentToolkit.cs`，第 145-152 行

```csharp
if (_scope.IsInteractionAllowed)
{
    if (_scope.SelectionHandler != null)
        Add(WorkflowToolCategory.Interaction, T(RequestSelection, nameof(RequestSelection)));
    if (_scope.ConfirmationHandler != null)
        Add(WorkflowToolCategory.Interaction, T(RequestConfirmation, nameof(RequestConfirmation)));
}
```

**2. 交互策略。** `WithSelectionHandler` / `WithConfirmationHandler` 把宿主的交互响应策略注入 `RequestSelection` / `RequestConfirmation` 工具背后，`WithInteractionSafety(0-3)` 选择这些工具被使用的急切程度（`0` = 完全自主、永不交互；`3` = 每个非平凡变更前都询问）。`ResolveConfirmationAsync` 按 `operationKey` 将会话内的 `AllowAlways` 决定记入缓存，因此所选的策略由代码强制，而不只是提示词（`WorkflowAgentScope.cs`，第 324-442 行）。

Demo 经 `AgentHelper.InteractionSafety`（默认 3）与可选的逐级提示词覆盖（`AgentHelper.InteractionSafetyPrompts`）按宿主设置交互策略——`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 139-150 行。
