# Workflow Agent — Design Patterns — Decorator

Every `AIFunction` tool — built-in and developer-registered alike — is wrapped by the private nested `TrackedAIFunction : DelegatingAIFunction`, so cross-cutting concerns are layered without changing any tool body:

1. **UI-thread marshalling** — when a `SynchronizationContext` is configured and the call is not already on it, the whole body runs through `context.Post`.
2. **Max-call pre-flight** — `MaxToolCalls` / `MaxReadToolCalls` / `MaxWriteToolCalls` are rejected before invocation.
3. **Exception capture** — a thrown exception becomes a JSON `{"status":"error"}` instead of an SDK failure.
4. **Tracking** — after success, `TrackAsync` increments the counters, raises `ToolCalled`/invokes the `WithToolCallCallback` handler, and (when `AutoMarkDirty` is enabled) marks the tree dirty unless the tool is a query tool.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, lines 178-242

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

This is the Decorator pattern: `WorkflowAgentToolkit` (the client) composes `DelegatingAIFunction` subclasses around the underlying `AIFunction` created by `AIFunctionFactory.Create`. Non-`AIFunction` tools (e.g. raw MCP client tools) bypass the decorator and are added as-is (`WorkflowAgentToolkit.cs`, lines 171-172).
