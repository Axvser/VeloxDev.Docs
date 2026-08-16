# Workflow System — Design Patterns — Strategy (runtime)

At runtime the flow can fall back to an earlier compile state. A node that calls `RuntimeContext.Error()/Warn()` or throws during `ReceiveAsync` requests a redirect; if it implements `IRedirectable`, the engine re-runs the whole graph from the returned `CompileContext.Order` (skipping earlier nodes, possibly cross-chain). This is the runtime counterpart of the compile-time routing strategy:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`, lines 96-148 and `IRedirectable.cs`

```csharp
if (node is not IRedirectable redirectable)
{
    context.CurrentOrder = -1;
    context.EndedWithError = true;
    context.Error("节点报告错误但未实现 IRedirectable，流程结束（状态 -1）。");
    return true;
}

var target = await redirectable.ResolveRedirectAsync(context, ct);
if (target is { } targetOrder && targetOrder < order)
{
    context.PendingRedirectTarget = targetOrder;
}
```

*Test evidence: `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/RedirectTests.cs` (`RedirectGate_RedirectsToChainHead_ThenSucceeds`, `RedirectCrossChain_SkipsPriorAndReruns`, `RedirectToRouter_ReroutesWithoutRecompute`).*
