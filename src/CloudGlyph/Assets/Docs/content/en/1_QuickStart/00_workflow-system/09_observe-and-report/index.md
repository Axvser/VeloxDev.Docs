# Workflow System — Observe a Run and Read Its Outcome

Two ways to watch a run: an `IExecutionObserver` gets its timeline, and `RunOutcome` gives `Status` a precise reading. Both live on the session created in `Install & Create the Project`.

## 1. Watch the timeline

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var observed = new List<string>();
var context = new RuntimeContext
{
    Observer = new DelegateExecutionObserver(o =>
    {
        if (o.Kind is ExecutionObservationKind.NodeStarted or ExecutionObservationKind.NodeSucceeded)
            observed.Add($"{o.Kind}:{o.Node?.GetType().Name}");
    }),
};

await new RuntimeEngine().RunAsync(rootGraph, context, CancellationToken.None);
Console.WriteLine(string.Join(", ", observed));
```

**Expected result:** one pair of lines per node, in drive order:

```text
NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
```

**Notes:** the three run- and branch-level kinds (`RunStarted`, `BranchStarted`, `RunEnded`) carry `Node == null`; each observation also carries `Attempt` (which pass it belongs to) and `Elapsed` (how long the step took). `ExecutionObservationKind` has seven members — `RunStarted`, `BranchStarted`, `NodeStarted`, `NodeSucceeded`, `NodeFailed`, `NodeRetried`, `RunEnded`. A throwing observer is swallowed and logged (`[Observer] …`): an observation is a diagnostic, not evidence.

## 2. Report a failure as a record

`IExecutionErrorSink` receives every failure the run records, as structured data rather than a log line:

```csharp
var records = new List<ExecutionError>();
var sinkContext = new RuntimeContext
{
    ErrorSink = new DelegateExecutionErrorSink(records.Add),
};

await new RuntimeEngine().RunAsync(rootGraph, sinkContext, CancellationToken.None);
Console.WriteLine($"records on a clean run: {records.Count}");
```

**Expected result:** `records on a clean run: 0` — nothing failed, so nothing was reported.

A node can report through the asynchronous pair, which also feeds the sink:

```csharp
// inside a NodeHelper<T>.ReceiveAsync override
public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
{
    if (context is IRuntimeContext rc && rc.Attempt == 2)
        await rc.ErrorAsync("the interpreter died");     // writes [Error] and records it
    else if (context is IRuntimeContext rc2)
        await rc2.WarnAsync("nothing to run");          // writes [Warning] and records it
    return context.Data;
}
```

**Expected result:** a warning records one entry with `Level == Warning` and lets the run continue with the node's own return value; an error records one entry at `Level == Error` and — unless the node implements `IRedirectable` — ends the flow with `Status == "Stopped"` and `CurrentOrder == -1`. The synchronous `Error` / `Warn` write the log line only, by design: they run inside a node's frame and must never block.

## 3. Read the outcome

`Status` has to share the one word `"Stopped"` between a failure and a cancellation, so read `Outcome` instead:

```csharp
var completed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, completed, CancellationToken.None);
Console.WriteLine($"{completed.Status} {completed.Outcome}");     // Completed Completed
```

**Expected result:** `Completed Completed`. The mapping is:

| `Outcome` | When |
|---|---|
| `Unknown` | the run has not ended — never started, or still going |
| `Completed` | `Status == "Completed"` — every entry was walked (a terminal branch that ends the run early is a completion) |
| `Cancelled` | `Status == "Stopped"` and `EndedWithError == false` — the host's token ended it |
| `Failed` | `Status == "Stopped"` and `EndedWithError == true` — a failure ended the flow |

**Notes:** a cancelled run deliberately writes **no** `[Error]` log line — a host stopping its own run is not a failure, and an `[Error]` line would make a later reader of `Logs` think one had happened. It still reports a `Run`-phase record to the sink, with `Node == null`.

## 4. Where this lives in the real repository

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` sets both in `ConfigureRun`: `context.Observer = new DelegateExecutionObserver(Observe);` and `context.ErrorSink = new DelegateExecutionErrorSink(Diagnostics.Add);` (where `Diagnostics` is an `ObservableCollection<ExecutionError>`). Its `Observe` counts `NodeStarted` / `NodeRetried` and writes **one** summary line on `RunEnded` — a run drives twenty-odd nodes and a line each would drown the log:

```text
[Observer] {nodes} nodes driven, {retries} retried, pass {attempt}, {seconds}s, {outcome}
```

Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionObserverTests.cs` and `ExecutionErrorSinkTests.cs` (the latter pins the recorded phase for a node throw, a node report, a router throw, a redirect-resolution throw, a host cancellation and the redirect cap).

Go to `Retry and compensate`.
