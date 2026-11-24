# Resilience contracts

Six capabilities let a host recover from, pause, watch or unwind a run. Each is optional, each is configured on `RuntimeContext`, and each is a bypass: with none configured the run behaves exactly as before.

- [Redirect and retry](00_redirect-and-retry/index.md) — a node's own fallback decision and the policy for thrown failures.
- [Gate and observer](01_gate-and-observer/index.md) — pausing between nodes, the run timeline, and the optional runtime notification.
- [Error sink and compensation](02_error-sink-and-compensation/index.md) — failures as records, and what a failed run already did.

All types are in `VeloxDev.Core.WorkflowSystem.CompilerEx`. The delegate-based implementations (`DelegateExecutionGate`, `DelegateExecutionObserver`, `DelegateExecutionErrorSink`, `DelegateExecutionCompensation`) are the one-liner forms; the interfaces are the seam.

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3),
    Observer = new DelegateExecutionObserver(o => Console.WriteLine(o.Kind)),
    ErrorSink = new DelegateExecutionErrorSink(e => Console.WriteLine(e.Message)),
};
```
