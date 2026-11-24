# Redirect and retry

A thrown exception is a failed drive; an `Error` call is a deliberate redirect request. Only throws are retried, and only when a retry policy is configured.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## IRedirectable

**Signature:** `interface IRedirectable`

| Member | Type | Description |
| --- | --- | --- |
| `ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` | `Task<INodeComponent?>` | Returns an upstream node to fall back to, or null to decline. |

The engine calls this when a drive reports `Error` or throws. The returned node must be an **upstream** compiled node of the requesting node; the engine maps it to that node's compile order, ends the pass there and re-runs the graph from the target, skipping earlier nodes. A router at or before the target is not driven again — only re-asked for its route key.

An invalid target is logged and ignored, and the flow carries on. The redirect cap is 50 passes.

## NodeFailure

**Signature:** `readonly record struct NodeFailure(INodeComponent Node, Exception Error, int RetryNumber, TimeSpan Elapsed)`

| Member | Type | Description |
| --- | --- | --- |
| `Node` | `INodeComponent` | The node that failed. |
| `Error` | `Exception` | What it threw. |
| `RetryNumber` | `int` | Which retry this decision is about; `1` for the first. |
| `Elapsed` | `TimeSpan` | How long the failed attempt took. |

## INodeRetryPolicy

**Signature:** `interface INodeRetryPolicy`

| Member | Type | Description |
| --- | --- | --- |
| `NextRetryAsync(NodeFailure failure, CancellationToken cancellationToken)` | `Task<TimeSpan?>` | Delay before the next attempt, or null to give the failure back to the engine. |

- Only thrown exceptions are retried. A node calling `Error`/`Warn` is making a control-flow request, not a failure to retry.
- `RetryNumber` starts at `1`; a policy that always returns a delay retries forever, since the run has no other cap.
- A retry is **not** an attempt: `IRuntimeContext.Attempt` counts passes over the graph and does not move.
- Cancellation is never retried. A policy that throws is treated as "do not retry".

## ExponentialBackoffRetry

**Signature:** `sealed class ExponentialBackoffRetry : INodeRetryPolicy`

**Constructor:** `ExponentialBackoffRetry(int maxAttempts = 3, double baseDelayMs = 200, double factor = 2.0, double maxDelayMs = 5000)`

| Parameter | Type | Description |
| --- | --- | --- |
| `maxAttempts` | `int` | Total attempts including the first; clamped to at least `1`. |
| `baseDelayMs` | `double` | Wait before the first retry; clamped to at least `0`. |
| `factor` | `double` | Multiplier per successive wait; clamped to at least `1`. |
| `maxDelayMs` | `double` | Ceiling on one wait; clamped to at least `baseDelayMs`. |

| Member | Type | Description |
| --- | --- | --- |
| `MaxAttempts` | `int` | The configured total. |
| `NextRetryAsync(NodeFailure, CancellationToken)` | `Task<TimeSpan?>` | Returns `baseDelay * factor^(RetryNumber-1)` capped at `maxDelayMs`, or null once `RetryNumber >= MaxAttempts`. |

The delay is a pure function of the retry number; nothing here inspects the exception. A policy that wants "retry a timeout but not a validation error" writes its own one-method implementation.

## Example

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RetryNode : IRedirectable
{
    public RetryNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }

    public Func<IRuntimeContext, INodeComponent?>? Redirect { get; set; }

    public Task<INodeComponent?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)
        => Task.FromResult(Redirect?.Invoke(context));
}

var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 10),
};
```
