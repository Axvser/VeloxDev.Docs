# Compiler entry

One method compiles a graph, and one enum chooses which way the walk goes.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## CompileRole

**Signature:** `enum CompileRole`

| Value | Meaning |
| --- | --- |
| `Root` | The node is a root starter; compile the subgraph reachable downstream along `Targets`. |
| `Terminal` | The node is a result terminal; walk `Sources` to collect its ancestor cone and compile only what is needed to compute it. |

## CompilerViewModel

**Signature:** `sealed partial class CompilerViewModel`

| Member | Type | Description |
| --- | --- | --- |
| `Graphs` | `ObservableCollection<CompiledGraph>` | The graphs produced by the most recent compile. |
| `CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)` | `Task<IReadOnlyList<CompiledGraph>>` | The single entry point; `T : IWorkflowComponent`. |

### CompileAsync

**Signature:** `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default) where T : IWorkflowComponent`

| Parameter | Type | Description |
| --- | --- | --- |
| `component` | `T` | Must be an `INodeComponent`; it plays `role`. |
| `role` | `CompileRole` | `Root` or `Terminal`. |
| `ct` | `CancellationToken` | Cancels between nodes and edges. |

**Returns:** `IReadOnlyList<CompiledGraph>` — always one graph in the current implementation. `Graphs` is cleared and refilled with it.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `ArgumentException` | `component` is not an `INodeComponent`. |
| `ArgumentOutOfRangeException` | `role` is not a defined value. |
| `InvalidOperationException` | Terminal mode: the router has more than one branch reaching the target, or the cone's independent producers do not funnel into one common join. |

The call is asynchronous because a router's `GetRouteTable`/`ResolveRouteKey` and each edge's `AccessAsync` are asynchronous. For `Root`, the walk starts at `component`; for `Terminal`, the compiler first builds the ancestor cone with a reverse BFS and then compiles the cone's own entry frontier.

## Decomposition rules

- A linear segment with one input and one output becomes a `ChainSegment`.
- An `ICompileTimeRouter` becomes a `BranchSegment`. A static key prunes unselected branches; a dynamic key keeps every option.
- A route key with several targets, or a plain node with several valid targets, becomes a `ParallelSegment`. The node all branch exits point to becomes the join point and the start of the next chain.
- Nodes already visited are not compiled again; the compiled graph is acyclic.
- Every edge is checked with `INodeHelper.AccessAsync` at compile time. A rejected edge is skipped exactly as an unconnected one would be at run time.
- In static mode, nodes of an unselected branch are visited and assigned `Order = -1` (the absolute stop state), and appear in no segment.
- Edges not accepted by `AccessAsync` do not appear in the graph.

Redirect is not part of the compiled graph; it is a runtime contract (`IRedirectable`).

## Example

```csharp
var compiler = new CompilerViewModel();
var root = await compiler.CompileAsync(startNode, CompileRole.Root);
Console.WriteLine(root.Count);                 // 1
Console.WriteLine(compiler.Graphs.Count);      // 1

var cone = await compiler.CompileAsync(targetNode, CompileRole.Terminal);
Console.WriteLine(cone[0].Entries.Count);
```
