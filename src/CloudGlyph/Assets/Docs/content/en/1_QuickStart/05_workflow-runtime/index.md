# Workflow runtime

`RuntimeEngine.RunAsync` drives a `CompiledGraph`, not the live canvas: it walks the compiled segments, calls each node's `ReceiveAsync`, and writes the returned value into the session for the next node. The graph decides the shape; the engine decides the path, the payload and how the run ends.

Three pages build up the runtime:

- [Execute a graph](00_execute-a-graph/index.md) — a chain, a fan-out with a keyed join, data flow, logs and outcomes.
- [Retry and redirect](01_retry-redirect/index.md) — thrown failures, `IRedirectable`, the error sink and compensation.
- [Pause, observe and checkpoint](02_pause-observe-checkpoint/index.md) — the execution gate, the observer, a file log writer, and resuming from a checkpoint.

All three use the same compiled graph. Every capability is optional and is configured on `RuntimeContext`; with none configured a run behaves as it always did.
