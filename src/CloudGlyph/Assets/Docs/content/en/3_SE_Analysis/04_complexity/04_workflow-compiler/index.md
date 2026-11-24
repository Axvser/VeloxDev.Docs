# Workflow compiler

`CompileAsync` walks a reachable subgraph once, decomposing it into chain, branch and parallel segments. The visited set makes the walk linear in the graph; the super-linear terms come from rescanning a node's slots at each decision point and from the reverse (ancestor-cone) mode, where predecessor lists are de-duplicated with a linear scan.

Notation: $V$ nodes, $E$ slot edges, $d$ the maximum degree of one node, $K$ route keys returned by a router, $S$ generated segments, $D$ branch-nesting depth, and $V_c$, $E_c$ the ancestor cone.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `CompileAsync`, Root | $O(V + E d)$ worst, $O(V + E)$ for bounded degree | $O(V + E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:38` |
| Linear chain walk | $O(V)$ | $O(V)$ visited set | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:69` |
| Router fan-out | $O(K \cdot \text{targets})$ per router | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:103` |
| Plain-node fan-out | $O(\text{valid targets})$ + one recursive compile each | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:223` |
| Static pruning BFS | $O(V_s + E_s)$ skipped subgraph | $O(V_s)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:308` |
| Edge validation | $O(E)$ awaits | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:443` |
| Reverse ancestor cone | $O(V_c + E_c d)$ worst | $O(V_c + E_c)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs:34` |
| Outline flattening | $O(S + N)$ | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Model/CompiledOutline.cs:35` |

## The walk is linear because of the visited set

Chains are followed in a loop, not by recursion, so a long linear graph does not grow the stack. A node compiled on a previous pass stops the walk:

```csharp
while (node != null)
{
    if (!ReferenceEquals(node, start) && !resumedAfterBranch && HasMultipleInputs(node, state.Cone))
        break;
    if (!state.Visited.Add(node))
        break;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:69-79`

The recursive calls happen only for branch and fan-out targets, so stack depth is $O(D)$, not $O(V)$. Each node is compiled once, which gives:

$$
T_{\text{compile}}(V,E) = O(V + E)
$$

for graphs whose nodes carry a bounded number of slots. `HasMultipleInputs`, `SingleTarget` and the target enumeration each rescan a node's own slots, which adds the $E d$ factor when one node has many ports.

## Where the extra factor comes from

Route keys and branch targets are paired in nested loops, and each target starts a recursive compile:

```csharp
foreach (var kv in routeTable)
{
    if (kv.Value.Count == 1)
        var sub = await CompileGraphAsync(target, state, ct);
    ...
    foreach (var t in kv.Value)
        var sub = await CompileGraphAsync(t, state, ct);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:103-139`

There is no concurrency: every router call and every `AccessAsync` rule check is awaited in sequence. "Parallel" segment construction is sequential work that merely *describes* runtime fan-out, so wall-clock time equals total work.

## Reverse mode is the weakest bound

Ancestor-cone mode builds predecessor lists and de-duplicates each predecessor with a linear `Any` scan:

```csharp
foreach (var source in slot!.Sources ?? [])
{
    ...
    if (!list.Any(p => ReferenceEquals(p, sender)))
        ...
    if (cone.Add(sender))
        queue.Enqueue(sender);
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs:50-67`

For a node with fan-in $F$, the dedupe is $O(F^2)$ per merge point. The reverse bound is therefore $O(V_c + E_c d)$ in the sparse case, and $O(\sum F^2)$ on dense fan-in.

```plot
{
  "title": "Compiler work: sparse graph vs dense fan-in",
  "grid": true,
  "xAxis": { "domain": [0, 80] },
  "yAxis": { "domain": [0, 6400] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(V + E), visited walk" },
    { "fn": "x*log(x+1)", "color": "#a78bfa", "title": "route table + target scan" },
    { "fn": "x*x", "color": "#f472b6", "title": "reverse dedupe, dense fan-in" }
  ]
}
```

## Memory

The compile state holds a visited set $O(V)$, a binding table $O(V)$ that the resulting graph retains, join-input lists $O(\text{joins})$, and the segment/option/branch lists $O(S + K \cdot \text{targets})$. The outline is a separate $O(S)$ list. The recursion stack is $O(D)$; linear chains are iterative and do not consume stack proportional to their length.
