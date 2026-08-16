# Workflow Agent — 设计模式 — 装饰器

私有嵌套类继承 `DelegatingAIFunction` 并覆写 `InvokeCoreAsync`：先预检调用上限，调用内部函数，再调用 `TrackAsync`（计数、回调、自动置脏）。配置了 `SynchronizationContext` 时还会把整个调用 marshal 到 UI 线程。

> 源码：`WorkflowAgentToolkit.cs`，第 175-239 行

```csharp
protected override async ValueTask<object?> InvokeCoreAsync(
    AIFunctionArguments arguments, CancellationToken cancellationToken)
{
    var uiContext = _toolkit._scope.UIContext;
    if (uiContext is not null && !ReferenceEquals(uiContext, SynchronizationContext.Current))
    {
        return await RunOnContextAsync(uiContext, cancellationToken,
            () => InvokeCoreInnerAsync(arguments, cancellationToken)).ConfigureAwait(false);
    }
    return await InvokeCoreInnerAsync(arguments, cancellationToken).ConfigureAwait(false);
}
```
