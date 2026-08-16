# Workflow Agent — Design Patterns — Decorator

The private nested class extends `DelegatingAIFunction` and overrides `InvokeCoreAsync` to pre-flight call limits, invoke the inner function, then call `TrackAsync` (counting, callback, auto-dirty). It also marshals the whole call onto the UI `SynchronizationContext` when one is configured.

> Source: `WorkflowAgentToolkit.cs`, lines 175-239

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
