# Workflow Agent — 设计模式 — 装饰器

每个 `AIFunction` 工具——内置与开发者注册的——都被顶层 `internal sealed TrackedAIFunction : DelegatingAIFunction`（声明于 `Agent/TrackedAIFunction.cs`，命名空间 `VeloxDev.AI`）包装，从而在不改动工具体的前提下叠加横切关注点：

1. **UI 线程 marshal** —— 配置了 `SynchronizationContext` 且当前不在其上时，整个工具体经 `context.Post` 运行。
2. **最大调用预检** —— 调用前先拒绝超限（`MaxToolCalls` / `MaxReadToolCalls` / `MaxWriteToolCalls`）。
3. **异常捕获** —— 抛出的异常变成 JSON `{"status":"error"}`，而非 SDK 级失败。
4. **上报** —— `ReportAsync` 把 `AgentToolCallStarted` / `AgentToolCallCompleted`（带结果与耗时）发布进作用域的 `AgentPipeline`；被拒绝或失败的调用同样会上报。计数器、`ToolCalled` 回调与自动置脏由下游的 `AccountingStage` 施加。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs`，第 29-143 行

```csharp
internal sealed class TrackedAIFunction(
    AIFunction inner,
    ToolPipeline? tools = null,
    AgentPipeline? pipeline = null) : DelegatingAIFunction(inner)
{
    private readonly ToolPipeline _tools = tools ?? new ToolPipeline();

    protected override async ValueTask<object?> InvokeCoreAsync(
        AIFunctionArguments arguments, CancellationToken cancellationToken)
    {
        // Components are UI-bound, so when the host configured a UI SynchronizationContext and we are not
        // already on it, marshal the entire call (body + reporting) onto it. Resolved per call, since the
        // host may register the context after this wrapper was built.
        var uiContext = _tools.ResolveContext();
        if (uiContext is not null && !ReferenceEquals(uiContext, SynchronizationContext.Current))
        {
            return await RunOnContextAsync(uiContext, cancellationToken,
                () => InvokeCoreInnerAsync(arguments, cancellationToken)).ConfigureAwait(false);
        }
        return await InvokeCoreInnerAsync(arguments, cancellationToken).ConfigureAwait(false);
    }
}
```

这是装饰器模式：`WorkflowAgentToolkit`（客户端）在 `AIFunctionFactory.Create` 创建的底层 `AIFunction` 之外组合 `DelegatingAIFunction` 子类。非 `AIFunction` 工具（如原始 MCP 客户端工具）绕过装饰器、原样加入（`WorkflowAgentToolkit.cs`，第 230-231 行）。
