# Compile-time contracts

A router declares its branches; the compiler asks for them twice, once for structure and once for the key. A node can also opt into a notification of its compile identity, but the authoritative copy lives on the graph.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## ICompileTimeRouter

**Signature:** `interface ICompileTimeRouter`

| Member | Type | Description |
| --- | --- | --- |
| `GetRouteTable()` | `Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>>` | Branch table: key → downstream nodes; one key may fan out to several. |
| `ResolveRouteKey(object? payload)` | `Task<object?>` | Returns the key for the current payload; called with `null` at compile time. |

At compile time, returning `null` from `ResolveRouteKey(null)` means "undecidable now", so the branch is dynamic and every option is kept. Returning a key makes the branch static and locks that value as `BranchSegment.CompileKey`. At run time a dynamic branch calls `ResolveRouteKey(context)` again with the session as payload.

An option whose node list is empty is terminal: choosing it at run time ends the run.

## RouterCompileMode

**Signature:** `enum RouterCompileMode`

| Value | Meaning |
| --- | --- |
| `Static` | `GetRouteTable` returns only the selected branch; the compiled graph is that single path. |
| `Dynamic` | `GetRouteTable` returns every branch; the run decides which one executes. |

`RouterCompileMode` is a convention a router may use to answer the two calls; the compiler never reads this enum.

## ICompileContext

**Signature:** `interface ICompileContext : IAccessContext`

| Member | Type | Description |
| --- | --- | --- |
| `Order` | `int` | Compile-fixed execution order; `-1` is the absolute stop. |
| `ChainIndex` | `int` | Index within the linear segment. |
| `Offset` | `int` | Subgraph entry offset. |
| `InputNodes` | `IReadOnlyList<INodeComponent>?` | Join inputs; null on chained and single-input nodes. |

Inherited from `IAccessContext`: `Data` (null at compile time), `Sender`, `Receiver`, `IsCompilePhase` (`true`).

## CompileContext

**Signature:** `sealed partial class CompileContext : ICompileContext`

Properties: `IsCompilePhase` (`true`), `Data` (`null`), `Sender` (`ISlotComponent?`), `Receiver` (`ISlotComponent?`), `InputNodes`, `Order` (default `-1`), `ChainIndex` (default `-1`), `Offset` (default `0`).

The compiler has two uses for it:

- **Edge validation** — a `CompileContext` filled with `Sender` and `Receiver` is passed to `INodeHelper.AccessAsync` for each output edge. Returning `false` drops the edge.
- **Identity notification** — after assigning a node's identity, the compiler passes a copy to `ICompileTimeAware`.

In both cases the payload is null: compile-time detection is static.

## ICompileTimeAware

**Signature:** `interface ICompileTimeAware`

| Member | Type | Description |
| --- | --- | --- |
| `AttachCompileTimeContext(ICompileContext context)` | `void` | Receives a snapshot once per compilation that reaches the node. |
| `CompileContext` | `ICompileContext?` | The last received snapshot, or null. |

The engine never reads this copy back. The authoritative identity is `CompiledGraph.TryGetCompileInfo`; a node that implements nothing still participates in joins, redirect skipping and status codes. An exception thrown from `AttachCompileTimeContext` is swallowed and does not fail compilation. Use it for a display concern such as a compile badge.

## Example

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter, ICompileTimeAware
{
    public RouterNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];
    public object? Selection { get; set; } = "A";

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(payload is null ? null : Selection);   // dynamic at compile time

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}
```
