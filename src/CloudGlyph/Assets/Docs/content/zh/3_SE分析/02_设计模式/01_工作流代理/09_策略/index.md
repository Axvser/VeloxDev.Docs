# 工作流代理 —— 设计模式 —— 策略

两个策略接缝让宿主选择 agent 的*行为方式*，而无需修改工具包：

**1. 工具表面选择。** `WorkflowToolCategory` 是 `[Flags]` 枚举（`Query`、`Mutation`、`Execution`、`Command`、`Graph`、`Layout`、`Analytics`、`State`、`Composite`、`Interaction`）。`CreateTools(categories)` 只注册选中的分组，降低每次请求的 token 成本并提升工具选择准确率。`Query` 只读；`Execution`/`Command` 组携带受能力闸门控制的工具；`Interaction` 在对应处理器存在时注册（已无安全档位闸门）。

> 源码：`WorkflowToolCategory.cs`；`WorkflowAgentToolkit.CreateAllTools`

```csharp
if (_scope.SelectionHandler != null)
    Add(WorkflowToolCategory.Interaction, T(RequestSelection, nameof(RequestSelection), AgentActionCategory.Interact));
if (_scope.ConfirmationHandler != null)
    Add(WorkflowToolCategory.Interaction, T(RequestConfirmation, nameof(RequestConfirmation), AgentActionCategory.Interact));
```

**2. 权限策略。** `WithPermissionMode(AgentPermissionMode)` 选择粗粒度决策矩阵（`Plan`、`Manual`、`AutoEdit`、`Auto`、`Bypass`）；`WithPermissionRule(decision, patterns)` 添加细粒度层；`WithPermissionJudge` 为 `Auto` 中无规则裁决的调用提供决定。策略在 `ToolPipeline.Confirm` 与 `CheckInvocation` 中逐次调用评估，因此由代码执行而非提示文本。`WithSelectionHandler` / `WithConfirmationHandler` 在 `RequestSelection` / `RequestConfirmation` 背后注入宿主的交互响应行为；`ResolveConfirmationAsync` 按 `operationKey` 本会话记住 `AllowAlways` 决定。

示例按宿主设置策略：`AgentHelper.PermissionMode`（默认 `AutoEdit`）与 `AgentHelper.PermissionRules`（对破坏性变更的 `Ask` 规则），在 `AgentHelper.ProvideAgent` 中用 `WithPermissionMode` / `WithPermissionRule` 应用。
