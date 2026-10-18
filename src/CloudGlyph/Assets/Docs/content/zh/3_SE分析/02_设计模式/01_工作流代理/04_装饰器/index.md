# 工作流代理 —— 设计模式 —— 装饰器

每个 `AIFunction` 工具 —— 内置与开发者注册的一样 —— 都被顶层 `internal sealed TrackedAIFunction : DelegatingAIFunction`（声明于 `Agent/TrackedAIFunction.cs`，命名空间 `VeloxDev.AI`）包装，因此横切关注点被分层加入，而不改动任何工具体：

1. **UI 线程编组** —— 配置了 `SynchronizationContext` 且调用不在其上时，整个函数体通过 `context.Post` 运行。
2. **调用前闸门** —— 预算与权限策略（`Allow`/`Ask`/`Deny`）在调用前评估。
3. **异常捕获** —— 抛出的异常变成 JSON `{"status":"error"}`，而不是 SDK 失败。
4. **报告** —— `ReportAsync` 把 `AgentToolCallStarted` / `AgentToolCallCompleted`（带结果与耗时）发布进作用域的 `AgentPipeline`；被拒绝或失败的调用也会报告。计数、`ToolCalled` 回调与自动标脏由下游 `AccountingStage` 施加。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs`

```csharp
internal sealed class TrackedAIFunction(
    AIFunction inner,
    ToolPipeline? tools = null,
    AgentPipeline? pipeline = null,
    AgentActionCategory category = AgentActionCategory.Execute,
    string? source = null) : DelegatingAIFunction(inner)
{
    private readonly ToolPipeline _tools = tools ?? new ToolPipeline();

    protected override async ValueTask<object?> InvokeCoreAsync(
        AIFunctionArguments arguments, CancellationToken cancellationToken)
    {
        // 组件与 UI 绑定；宿主配置了 UI SynchronizationContext 且当前不在其上时，
        // 把整个调用（函数体 + 报告）编组过去。按调用解析，因为宿主可能在此包装器
        // 构建之后才注册上下文。
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

这就是装饰器模式：`WorkflowAgentToolkit`（客户端）把 `DelegatingAIFunction` 子类组合到 `AIFunctionFactory.Create` 产出的底层 `AIFunction` 周围。非 `AIFunction` 工具（如原始 MCP 客户端工具）绕过装饰器，按原样加入。
