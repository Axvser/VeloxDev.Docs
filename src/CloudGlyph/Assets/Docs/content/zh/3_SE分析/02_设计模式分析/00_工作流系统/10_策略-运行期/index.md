# Workflow System — 设计模式 — 策略（运行期）

重定向是编译期路由策略的运行期对应物：`ReceiveAsync` 期间的节点内 `Error()`/`Warn()`/异常被视为*重定向请求*，节点通过 `IRedirectable` 选择恢复策略。若实现了 `IRedirectable`，`RuntimeEngine.RunExecuteAsync` 调用 `ResolveRedirectAsync`；返回一个前驱 `Order` 会让引擎**朝向该编译状态重跑整张图**（`Order < target` 的节点被跳过，可跨链）。若目标就是 Router 自身，引擎只重新路由、不重算它。若节点**没有**实现 `IRedirectable`，整个流程以绝对停止状态 `-1` 结束：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`，第 136-158 行

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

`RunAsync`（第 19-68 行）把重定向统一实现为又一次整图 pass：每次 `RunAsync` 开头清一次产物登记表，随后每 pass 写 `Attempt`、`ActiveRedirectTarget`（当前目标 Order）与 `PendingRedirectTarget`。陈旧产物按 pass 戳过滤，汇合点不会聚合已被重跑取代的结果；目标之前的节点属“契约保留前缀”，其产物仍有效（`RuntimeContext.CollectGroupedInputs`/`IsCurrentPassOrPreserved`）。超过 50 次重定向抛 `InvalidOperationException` 放弃。

*测试证据：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/RuntimeRedirectTests.cs`——`RedirectToPredecessor_SkipsPrefixOnRerun_CountsNodesPerPass`、`RedirectTargetNotAPredecessor_IsIgnored_FlowCompletesSinglePass`、`RedirectToRouter_ReroutesOnly_WithoutRecomputingRouter`、`RedirectLoopsExceedingLimit_AbortWithException`。*
