# Workflow Agent — 设计模式 — 装饰器

每个 `AIFunction` 工具——内置与开发者注册的——都被私有嵌套类 `TrackedAIFunction : DelegatingAIFunction` 包装，从而在不改动工具体的前提下叠加横切关注点：

1. **UI 线程 marshal** —— 配置了 `SynchronizationContext` 且当前不在其上时，整个工具体经 `context.Post` 运行。
2. **最大调用预检** —— 调用前先拒绝超限（`MaxToolCalls` / `MaxReadToolCalls` / `MaxWriteToolCalls`）。
3. **异常捕获** —— 抛出的异常变成 JSON `{"status":"error"}`，而非 SDK 级失败。
4. **追踪** —— 成功后 `TrackAsync` 递增计数器、触发 `ToolCalled`/调用 `WithToolCallCallback` 处理器，且（启用 `AutoMarkDirty` 时）除非是查询工具否则将树置脏。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，第 178-242 行

```csharp
private sealed class TrackedAIFunction(AIFunction inner, WorkflowAgentToolkit toolkit) : DelegatingAIFunction(inner)
{
    protected override async ValueTask<object?> InvokeCoreAsync(
        AIFunctionArguments arguments, CancellationToken cancellationToken)
    {
        // Workflow components are UI-bound, so when the host configured a UI SynchronizationContext
        // and we are not already on it, marshal the entire tool call (body + tracking) onto it.
        var uiContext = _toolkit._scope.UIContext;
        if (uiContext is not null && !ReferenceEquals(uiContext, SynchronizationContext.Current))
        {
            return await RunOnContextAsync(uiContext, cancellationToken,
                () => InvokeCoreInnerAsync(arguments, cancellationToken)).ConfigureAwait(false);
        }
        return await InvokeCoreInnerAsync(arguments, cancellationToken).ConfigureAwait(false);
    }
}
```

这是装饰器模式：`WorkflowAgentToolkit`（客户端）在 `AIFunctionFactory.Create` 创建的底层 `AIFunction` 之外组合 `DelegatingAIFunction` 子类。非 `AIFunction` 工具（如原始 MCP 客户端工具）绕过装饰器、原样加入（`WorkflowAgentToolkit.cs`，第 171-172 行）。
