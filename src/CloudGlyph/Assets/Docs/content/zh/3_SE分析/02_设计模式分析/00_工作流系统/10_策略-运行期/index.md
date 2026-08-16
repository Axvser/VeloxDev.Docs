# Workflow System — 设计模式 — 策略（运行期）—— 重定向 / 错误处理

运行期流程可以回退到更早的编译状态。节点在 `ReceiveAsync` 中调用 `RuntimeContext.Error()/Warn()` 或抛异常即请求重定向；若实现 `IRedirectable`，引擎按返回的 `CompileContext.Order` 重跑整张图（跳过目标之前的节点，可跨链）。这是编译期路由策略的运行期对应物：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`，第 96-148 行；`IRedirectable.cs`

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

*测试证据：`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/RedirectTests.cs`（`RedirectGate_RedirectsToChainHead_ThenSucceeds`、`RedirectCrossChain_SkipsPriorAndReruns`、`RedirectToRouter_ReroutesWithoutRecompute`）。*
