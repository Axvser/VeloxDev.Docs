# Workflow System — Design Patterns — Strategy (runtime)

Redirect is the runtime counterpart of the compile-time routing strategy: an in-node `Error()`/`Warn()`/exception during `ReceiveAsync` is treated as a *redirect request*, and the node — through `IRedirectable` — selects the strategy for recovering. If it implements `IRedirectable`, `RuntimeEngine.RunExecuteAsync` calls `ResolveRedirectAsync`; a returned predecessor `Order` makes the engine **re-run the whole graph toward that compile state** (nodes with `Order < target` are skipped, possibly cross-chain). If the target is the router itself, the engine only re-routes without recomputing it. If the node does **not** implement `IRedirectable`, the whole flow ends with the absolute-stop status `-1`.

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`, lines 136-157

```csharp
if (!context.RedirectRequested) continue;

// Node errored but does not implement IRedirectable → the whole flow ends with status -1.
if (node is not IRedirectable redirectable)
{
    context.CurrentOrder = -1;
    context.EndedWithError = true;
    context.Error("Node reported an error but does not implement IRedirectable; the flow ends (status -1).");
    return true;
}

// With IRedirectable → its interface decides the redirect target (possibly cross-chain).
// Only a predecessor state (Order < current) is accepted.
var target = await redirectable.ResolveRedirectAsync(context, ct);
if (target is { } targetOrder && targetOrder < order)
{
    context.PendingRedirectTarget = targetOrder;
}
else
{
    context.Log($"Redirect target #{target} is not a predecessor or is invalid; ignored.");
}
```

`RunAsync` implements a redirect uniformly as another graph pass: it clears the output registry once per `RunAsync`, then each pass writes `Attempt`, `ActiveRedirectTarget` (the current target Order) and `PendingRedirectTarget`. Stale outputs from an earlier pass are filtered by pass stamp so a join never aggregates results the re-run superseded; nodes before the redirect target are the contract-preserved prefix whose outputs remain valid (`RuntimeContext.CollectGroupedInputs`, `IsCurrentPassOrPreserved`). More than 50 redirects abort with `InvalidOperationException`.

*Test evidence: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/RuntimeRedirectTests.cs` — `RedirectToPredecessor_SkipsPrefixOnRerun_CountsNodesPerPass`, `RedirectTargetNotAPredecessor_IsIgnored_FlowCompletesSinglePass`, `RedirectToRouter_ReroutesOnly_WithoutRecomputingRouter`, `RedirectLoopsExceedingLimit_AbortWithException`.*
