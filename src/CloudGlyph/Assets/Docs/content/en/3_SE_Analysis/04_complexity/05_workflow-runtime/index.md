# Workflow runtime

`RunAsync` drives a compiled graph. The structural pass is linear, fan-out is interleaved async rather than thread-parallel, and the costs that surprise are in bookkeeping: the output registry scans a growing completion list on every successful node, and a checkpoint save scans the output table per node. With checkpointing enabled on a wide graph, per-pass work becomes cubic.

Notation: $V$ nodes, $E$ edges, $B$ branches in one fan-out, $R$ redirects (capped at 50), $X$ checkpoint saves, $D$ nesting depth.

## Cost model

| Operation | Time | Source |
|---|---|---|
| `RunAsync` entry | $O(V)$ graph walk + $O(R \cdot \text{pass})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:56` |
| One structural pass | $O(V + E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:145` |
| Per-node drive | $O(1)$ + $O(\text{indeg})$ join + retry loop | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:507` |
| Output registration | $O(V)$ per success — **$O(V^2)$ per pass** | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/RuntimeContext.cs:391` |
| Checkpoint save | $O(V^2)$ per success, **$O(V^3)$ per pass** | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:764` |
| Parallel fan-out | total work $\sum_B$; wall clock overlaps at awaits | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:413` |
| Redirect | restarts the graph, bounded by 50 | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:94` |
| Upstream test | $O(V + E)$ reverse BFS, per redirect validation | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:501` |
| Compensation | $O(V)$ reverse order | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:671` |

## The structural pass

Entries are dispatched in order, and a chain is one loop over its nodes with constant-time order lookups from the binding table:

```csharp
for (int i = 0; i < exec.Nodes.Count; i++)
{
    ...
    if (done?.Contains(node) == true)
        ...
    await DriveAsync(node, context, bindings, ct);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:192-219`

A redirect does not resume in place. It restarts the graph with a target order, skipping nodes before it:

```csharp
while (true)
{
    var terminated = await RunGraphAsync(graph, context, bindings, ct, redirectTarget, redirects == 0 ? done : null);
    if (!terminated && context.PendingRedirectTarget is { } next)
    {
        redirects++;
        if (redirects > MaxRedirects)
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:94-109`

Because `MaxRedirects` is 50, the worst case is 51 structural passes, not unbounded retry.

## Fan-out is async interleaving, not thread parallelism

Branches are launched as tasks and awaited together:

```csharp
for (int i = 0; i < count; i++)
{
    branchContexts[i] = new BranchRuntimeContext(context) { Data = sourceData };
    tasks[i] = RunOneBranchAsync(branches[i], branchContexts[i], bindings, i, ct, redirectTarget, done, gate);
}

var terminated = await Task.WhenAll(tasks);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:437-443`

Total work is the sum over branches. Wall-clock time only falls when node bodies actually suspend (I/O); CPU-bound bodies run in turn on the host thread. An optional semaphore caps in-flight branches per group.

## The quadratic bookkeeping

Registration stamps the output and rebuilds the completion list by removing any earlier entry for the same node:

```csharp
_outputs[node] = (Attempt, value);
...
_completed.RemoveAll(entry => ReferenceEquals(entry.Node, node));
_completed.Add((node, value));
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/RuntimeContext.cs:394-400`

That `RemoveAll` is $O(V)$, once per successful node, so output bookkeeping is $O(V^2)$ per pass. When a checkpoint store is configured, a save additionally walks the output table and performs a linear key lookup per entry, which is another $O(V^2)$ per success — $O(V^3)$ per pass:

$$
T_{\text{pass}}^{\text{checkpoint}}(V,E) = O(V + E + V^3)
$$

```plot
{
  "title": "Runtime bookkeeping per pass",
  "grid": true,
  "xAxis": { "domain": [0, 40] },
  "yAxis": { "domain": [0, 64000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "structural pass, O(V)" },
    { "fn": "x*x", "color": "#a78bfa", "title": "output registry, O(V^2)" },
    { "fn": "x*x*x", "color": "#f472b6", "title": "checkpoint per success, O(V^3)" }
  ]
}
```

Disabling the checkpoint store removes the cubic term entirely; the registry remains quadratic but a completion list of a few hundred nodes makes it negligible in practice.

## Memory

The context keeps an output table $O(V)$, a completion list $O(V)$, and a checkpoint with three collections $O(V)$ each. Fan-out adds $O(B)$ branch contexts and tasks per group, and nesting adds $O(D)$ stack. Logs are retained without a cap by default; when a cap is configured, trimming removes from the front of an `ObservableCollection`, which is $O(n)$ per removed line.
