# 工作流系统 — 设计模式 — 策略（运行时）

重定向是编译期路由策略的运行期对应物：节点内的 `Error()` —— 或 `ReceiveAsync` 期间节点未捕获的异常 —— 被视为*重定向请求*，节点通过 `IRedirectable` 选择恢复策略。（`Warn()` 不是：它只是一条注记，运行带着节点返回值继续。）若节点实现 `IRedirectable`，`RuntimeEngine` 调用 `ResolveRedirectAsync`；返回的前驱 `Order` 让引擎**朝那个编译状态重跑整张图**（`Order < target` 的节点被跳过，可能跨链）。若目标就是路由器本身，引擎只重新路由而不重算它。若节点**没有**实现 `IRedirectable`，整个流程以绝对停止状态 `-1` 结束。

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`，204-244 行

```csharp
if (reported is null or ExecutionReportLevel.Warning) continue;

// Node errored but does not implement IRedirectable → the whole flow ends with status -1.
if (node is not IRedirectable redirectable)
{
    context.CurrentOrder = -1;
    context.EndedWithError = true;
    await ReportErrorAsync(session, context, ExecutionFailurePhase.Node, node,
        "Node reported an error but does not implement IRedirectable; the flow ends (status -1).", null, ct);
    return true;
}

// With IRedirectable → its interface decides the redirect target (possibly cross-chain).
// Only a predecessor state (Order < current) is accepted.
int? target;
try
{
    target = await redirectable.ResolveRedirectAsync(context, ct);
}
catch (OperationCanceledException)
{
    throw;
}
catch (Exception ex)
{
    context.CurrentOrder = -1;
    context.EndedWithError = true;
    await ReportErrorAsync(session, context, ExecutionFailurePhase.Redirect, node, ex.Message, ex, ct);
    return true;
}

if (target is { } targetOrder && targetOrder < order)
{
    context.PendingRedirectTarget = targetOrder;
}
else
{
    context.Log($"Redirect target #{target} is not a predecessor or is invalid; ignored.");
}
```

`RunAsync` 把重定向统一实现为又一次图遍历：每次 `RunAsync` 清空一次输出注册表，随后每一趟写入 `Attempt`、`ActiveRedirectTarget`（当前目标 Order）与 `PendingRedirectTarget`。上一趟的过期输出按趟戳过滤，join 因此绝不会聚合被重跑取代的结果；重定向目标之前的节点是契约保留前缀，其输出仍然有效（`RuntimeContext.CollectGroupedInputs`、`IsCurrentPassOrPreserved`）。超过 50 次重定向会以 `InvalidOperationException` 中止。

*测试证据：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/RuntimeRedirectTests.cs` —— `RedirectToPredecessor_SkipsPrefixOnRerun_CountsNodesPerPass`、`RedirectTargetNotAPredecessor_IsIgnored_FlowCompletesSinglePass`、`RedirectToRouter_ReroutesOnly_WithoutRecomputingRouter`、`RedirectLoopsExceedingLimit_AbortWithException`。*
