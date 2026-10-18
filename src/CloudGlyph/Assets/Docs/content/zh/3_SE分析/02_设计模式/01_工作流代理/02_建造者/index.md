# 工作流代理 —— 设计模式 —— 建造者

`WorkflowAgentScope` 是可变、流式的建造者：每个 `With*` 方法修改同一实例并返回 `this`，因此配置可以链式书写，也可以拆到不同调用点。终结方法（`Provide*`、`CreateToolkit`、`ProvideTools`）物化已配置状态 —— 内置提示由 `ProvideProgressiveContextPrompt()` / `ProvideAllContexts()` 组装，工具列表由 `ProvideTools()` 产出。

示例在一处接线整条建造者链（`AgentHelper.ProvideAgent`）：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，`ProvideAgent`

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)   // 默认提示语言
    .WithOutputLanguage(AgentLanguages.Chinese)   // 默认输出语言
    .WithAutoDiscovery()                    // 注册编译上下文树携带的类型
    .WithAutoMarkDirty(false)               // 视图是否自动标脏
    .WithMaxToolCalls(200)                  // 最大工具调用数
    .WithAllowNodeExecution(true)           // 允许 Agent 运行节点业务代码（默认关闭）
    .WithSynchronizationContext(SynchronizationContext.Current) // 把工具调用编组到 UI 线程
    .WithToolCallCallback(args =>           // 工具调用回调
    {
        helper.ToolCalled?.Invoke();
        helper.RecordToolCall(args);
        return Task.CompletedTask;
    })
    .WithSelectionHandler(async args =>      // Agent 询问用户要执行哪个动作
    {
        if (helper.SelectionHandler is not null)
            await helper.SelectionHandler(args);
    })
    .WithConfirmationHandler(async args =>   // Agent 询问用户确认某个操作
    {
        if (helper.ConfirmationHandler is not null)
            await helper.ConfirmationHandler(args);
    });

// 先权限模式，再用规则细化。
scope.WithPermissionMode(helper.PermissionMode);
foreach (var (decision, pattern) in helper.PermissionRules)
    scope.WithPermissionRule(decision, pattern);
```

因为终结方法读取累积状态，若干 `With*` 调用可以拆到不同方法（示例在链之后应用模式与规则），随后同一作用域既产出系统提示又产出工具列表，保证两者保持一致。

> `With*` 实现源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`。
