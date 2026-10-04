# Workflow Agent — Design Patterns — Decorator

Every `AIFunction` tool — built-in and developer-registered alike — is wrapped by the top-level `internal sealed TrackedAIFunction : DelegatingAIFunction` (declared in `Agent/TrackedAIFunction.cs`, namespace `VeloxDev.AI`), so cross-cutting concerns are layered without changing any tool body:

1. **UI-thread marshalling** — when a `SynchronizationContext` is configured and the call is not already on it, the whole body runs through `context.Post`.
2. **Max-call pre-flight** — `MaxToolCalls` / `MaxReadToolCalls` / `MaxWriteToolCalls` are rejected before invocation.
3. **Exception capture** — a thrown exception becomes a JSON `{"status":"error"}` instead of an SDK failure.
4. **Reporting** — `ReportAsync` publishes `AgentToolCallStarted` / `AgentToolCallCompleted` (with the outcome and elapsed time) into the scope's `AgentPipeline`; a refused or failed call is reported too. The counters, the `ToolCalled` callback and auto-dirty marking are applied downstream by the `AccountingStage`.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs`, lines 29-143

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

This is the Decorator pattern: `WorkflowAgentToolkit` (the client) composes `DelegatingAIFunction` subclasses around the underlying `AIFunction` created by `AIFunctionFactory.Create`. Non-`AIFunction` tools (e.g. raw MCP client tools) bypass the decorator and are added as-is (`WorkflowAgentToolkit.cs`, lines 230-231).
