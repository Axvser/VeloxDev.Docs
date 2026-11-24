# Compiled model

A `CompiledGraph` is an ordered collection of segments; segments nest. The graph also owns each node's compile identity in a binding table, so the runtime never asks a node to carry compiler state.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## CompiledGraph

**Signature:** `sealed partial class CompiledGraph`

| Member | Type | Description |
| --- | --- | --- |
| `Entries` | `ObservableCollection<CompileSegment>` | Ordered top-level segments. |
| `TryGetCompileInfo(INodeComponent node, out NodeCompileInfo? info)` | `bool` | Reads the node's compile identity from this graph. |

`TryGetCompileInfo` returns `false` for a node never compiled into the graph, for a pruned node, and for a graph restored from a document (bindings are runtime-only and not serialized). The binding dictionary itself is internal; this method is the public read.

## CompileSegment

**Signature:** `abstract partial class CompileSegment`

| Member | Type | Description |
| --- | --- | --- |
| `Id` | `Guid` | Segment identifier for a UI tree. |
| `Depth` | `int` | Nesting depth for indentation. |

## ChainSegment

**Signature:** `sealed partial class ChainSegment : CompileSegment`

| Member | Type | Description |
| --- | --- | --- |
| `Nodes` | `ObservableCollection<INodeComponent>` | The linear segment, in drive order. |

## BranchSegment

**Signature:** `sealed partial class BranchSegment : CompileSegment`

| Member | Type | Description |
| --- | --- | --- |
| `Router` | `INodeComponent?` | The router node. |
| `Options` | `ObservableCollection<BranchOption>` | One option per route key. |
| `IsDynamic` | `bool` | `true` when the key is resolved at run time. |
| `CompileKey` | `object?` | The static key locked at compile time; null for a dynamic branch. |
| `CompileKeyTypeName` | `string?` | The key's assembly-qualified type name when it is an enum; null otherwise. |

`CompileKeyTypeName` exists because an enum held in an `object` member round-trips as its underlying number. `BranchSegment` and `BranchOption` restore the enum on load, so a dynamic key re-resolved as a real enum still matches its option.

## ParallelSegment

**Signature:** `sealed partial class ParallelSegment : CompileSegment`

| Member | Type | Description |
| --- | --- | --- |
| `Branches` | `ObservableCollection<CompiledGraph>` | One child graph per fan-out branch. |

Branches are executed concurrently as interleaved async operations (see [Runtime engine](../../05_workflow-runtime/00_runtime-engine/index.md)), but the segment's shape is order-independent.

## BranchOption

**Signature:** `sealed partial class BranchOption`

| Member | Type | Description |
| --- | --- | --- |
| `Key` | `object?` | Route key. |
| `Label` | `string?` | Display label; defaults to the key's text. |
| `Graph` | `CompiledGraph?` | Downstream subgraph; null on a terminal option. |
| `IsTerminal` | `bool` | Selecting this option ends the whole run. |
| `KeyTypeName` | `string?` | The key's type name when it is an enum; used to restore the key on load. |

## NodeCompileInfo

**Signature:** `sealed class NodeCompileInfo` — constructor is internal; instances are created by the compiler.

| Member | Type | Description |
| --- | --- | --- |
| `Order` | `int` | Global drive order; `-1` is the absolute stop state. |
| `ChainIndex` | `int` | Index within the linear segment. |
| `Offset` | `int` | Entry offset of the subgraph the node belongs to. |
| `InputNodes` | `IReadOnlyList<INodeComponent>?` | Upstream sources a join aggregates; null on chained and single-input nodes. |

## CompiledOutline and CompiledOutlineRow

**Signature:** `static class CompiledOutline` with `readonly record struct CompiledOutlineRow(int Depth, string Kind, string Label, IReadOnlyList<INodeComponent> Nodes)`

| Member | Type | Description |
| --- | --- | --- |
| `CompiledOutline.Of(CompiledGraph graph)` | `IReadOnlyList<CompiledOutlineRow>` | Depth-first flattening, outermost first; empty for a null graph. |
| `CompiledOutlineRow.Depth` | `int` | Nesting depth, `0` at the graph's own entries. |
| `CompiledOutlineRow.Kind` | `string` | `Execute`, `Branch`, `Parallel`, `Option` or `Terminal`. |
| `CompiledOutlineRow.Label` | `string` | Node types joined with `→`, or the router and its option count. |
| `CompiledOutlineRow.Nodes` | `IReadOnlyList<INodeComponent>` | Nodes this row names; empty for option and parallel rows. |

`CompiledOutline` is the flat, virtualizable view of the same structure; the graph itself is already a bindable nested view model, so a flat outline is optional.

## Example

```csharp
var graph = (await new CompilerViewModel().CompileAsync(source, CompileRole.Root))[0];

foreach (var row in CompiledOutline.Of(graph))
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind}: {row.Label}");

if (graph.TryGetCompileInfo(source, out var info))
    Console.WriteLine(info!.Order);     // 0

var branch = graph.Entries.OfType<BranchSegment>().FirstOrDefault();
Console.WriteLine(branch?.Options.Count);
```
