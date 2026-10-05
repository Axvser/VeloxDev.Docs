# Workflow System — Compile Pipeline

The compile half of `VeloxDev.Core.WorkflowSystem.CompilerEx`: the entry point, the immutable artifact it produces, and the contracts a node implements to take part in compilation.

Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/` — `CompilerViewModel.cs`, `CompilerViewModel.Reverse.cs`, `CompileRole.cs`, `Contracts/`, `Model/`.

---

## Compile entry point

### `CompilerViewModel`

`public sealed partial class`. Held on a node (typically a controller) so the UI can bind the compile results — `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` declares `public CompilerViewModel Compiler { get; } = new();`.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Graphs` | `ObservableCollection<CompiledGraph>` | Latest compile output (`[VeloxProperty]`); UI-bound. Cleared at the start of every `CompileAsync`. |

##### Methods

#### `CompilerViewModel.CompileAsync<T>`

**Signature:**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(
    T component, CompileRole role, CancellationToken ct = default) where T : IWorkflowViewModel;
```

| Parameter | Type | Description |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | The node to compile from. Must be an `IWorkflowNodeViewModel` — under `Root` it is the starter; under `Terminal` it is the result node. |
| `role` | `CompileRole` | `Root` (forward) or `Terminal` (reverse ancestor cone). |
| `ct` | `CancellationToken` | Optional cancellation. Defaults to `default`. |

**Returns:** `IReadOnlyList<CompiledGraph>` — one compiled graph for the request. It is also pushed onto `Graphs`.

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentException` | `component` is not an `IWorkflowNodeViewModel`. |
| `ArgumentOutOfRangeException` | `role` is not a defined `CompileRole`. |
| `InvalidOperationException` | A `CompileRole.Terminal` cone cannot be expressed: independent producers do not funnel into one common join, or a router has more than one branch reaching the terminal. |

**Example:**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// Demo: Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs (the Compile command)
await Compiler.CompileAsync(this, CompileRole.Root);
```

**Notes:** `Terminal` is implemented in `CompilerViewModel.Reverse.cs`: a reverse BFS over slot `Sources` (each edge validated by the sender's `AccessAsync` with an `ICompileContext`), then the cone's entry frontier is derived automatically and only the cone is compiled. A router on the cone keeps real `BranchSegment` semantics with only the in-cone branch compiled (`RestrictRouteToCone`).

---

## Compile results

### `CompileRole`

**Signature:** `public enum CompileRole { Root, Terminal }`

| Member | Value | Meaning |
|---|---|---|
| `Root` | 0 | The node is a starter: compile the sub-graph reachable from it downstream along `Targets`. |
| `Terminal` | 1 | The node is a result terminal: compile its ancestor cone, computing only up to that node. |

### `CompiledGraph`

`public sealed partial class`. An ordered collection of compiled segments treated as one graph. Nestable — `BranchSegment` / `ParallelSegment` each hold child `CompiledGraph`s. Immutable once produced: it *describes* possible executions; which path actually runs is a runtime decision.

| Name | Type | Description |
|---|---|---|
| `Entries` | `ObservableCollection<CompileSegment>` | Top-level segments, in drive order. |

### `CompileSegment`

`public abstract partial class`. Shared base for the three concrete segment kinds.

| Name | Type | Description |
|---|---|---|
| `Id` | `Guid` | Segment UID (the UI tree-node identifier); defaults to `Guid.NewGuid()`. |
| `Depth` | `int` | Nesting depth, for UI indentation; defaults to `0`. |

| Segment | Members | Emitted for |
|---|---|---|
| `ChainSegment` (`sealed partial`) | `ObservableCollection<IWorkflowNodeViewModel> Nodes` | A single-in / single-out linear run of nodes. |
| `BranchSegment` (`sealed partial`) | `IWorkflowNodeViewModel? Router`, `ObservableCollection<BranchOption> Options`, `bool IsDynamic`, `object? CompileKey`, `string? CompileKeyTypeName` | A node implementing `ICompileTimeRouter`. |
| `ParallelSegment` (`sealed partial`) | `ObservableCollection<CompiledGraph> Branches` | A fan-out group: one route key feeding several targets, or several producers joining into one node. |

### `BranchOption`

`public sealed partial class`. One branch of a `BranchSegment`.

| Name | Type | Description |
|---|---|---|
| `Key` | `object?` | The route key this option answers to. |
| `Label` | `string?` | Display label (the key's string form; `"?"` when the key is null). |
| `Graph` | `CompiledGraph?` | The option's downstream sub-graph; `null` when the option is terminal. |
| `IsTerminal` | `bool` | No downstream node: selecting this option at runtime ends the whole run (the join tail is not propagated). |
| `KeyTypeName` | `string?` | Assembly-qualified key type, recorded by the compiler **only when the key is an enum** — see `CompileKeyNormalizer` below. |

### `CompileKeyNormalizer` *(internal)*

`internal static class`. Not part of the public surface; documented here because it explains a serialization behavior that would otherwise look like a bug.

A branch key is held as `object` because an `ICompileTimeRouter` may key its routes by anything, and a number comes back from JSON as `long`: an enum inside an `object` member returns as its underlying number, because enums are written as bare integers with no type tag (pinned by `ComponentModelExTests.AnEnumInAnObjectMember_ComesBackAsItsNumber`). A *static* branch survives that by luck — both sides degrade to `long` and still compare equal — but a *dynamic* branch re-resolves a real enum at run time and would then match no option at all, ending the run as if the branch had no downstream.

So the compiler records the key's type beside it (`CompileKeyNormalizer.TypeNameOf`) and `BranchSegment` / `BranchOption` restore the value on load through an `[OnDeserialized]` callback that calls `CompileKeyNormalizer.Normalize` — a callback rather than a property setter, because on load a setter would fire before a type-name member declared later in the document had been read. A number that matches no member becomes an *undefined* enum value rather than an error, which is exactly what a live run does with a key no option names.

---

## Compile-time contracts

| Type | Signature / members |
|---|---|
| `ICompileContext : IAccessContext` | `int Order { get; set; }` — compile-time fixed execution order, `-1` = absolute stop; `int ChainIndex { get; set; }` — index within the linear segment; `int Offset { get; set; }` — sub-graph entry offset; `IReadOnlyList<IWorkflowNodeViewModel>? InputNodes { get; set; }` — join-point input sources. |
| `CompileContext : ICompileContext` | `public sealed partial class`. `IsCompilePhase => true`, `Data => null`. `Sender` / `Receiver` are `null` on the identity instance a node holds and are filled only on the per-edge instances the compiler builds for `AccessAsync`. `Order` / `ChainIndex` / `Offset` are `[VeloxProperty]` with defaults `-1` / `-1` / `0`. |
| `ICompileTimeAware` | `void AttachCompileTimeContext(ICompileContext context)`; `ICompileContext? CompileContext { get; }` — injects the compile identity when compilation finishes. |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()` — branch table (one key may fan out to several targets); `Task<object?> ResolveRouteKey(object? payload)` — the route key for the current payload (`IRuntimeContext` at run time, `null` at compile time). |
| `RouterCompileMode` | `public enum RouterCompileMode { Static, Dynamic }`. `Static`: `GetRouteTable()` returns only the currently selected branch and order is fixed at compile time. `Dynamic`: all branches stay alive and the key is re-resolved at run time. |

`CompileKey` on a `BranchSegment` is what `ResolveRouteKey(null)` returned at compile time: a non-null key means **Static** (`IsDynamic == false`) and runtime uses the locked key; `null` means **Dynamic** (`IsDynamic == true`) and runtime calls `ResolveRouteKey(context)`. Under static pruning every reachable-but-unselected node is stamped `Order = -1` and never enters a segment.

See `Strategy pattern` for the demo router that implements this contract.

---

## Flattened outline

### `CompiledOutline` / `CompiledOutlineRow`

```csharp
public readonly record struct CompiledOutlineRow(
    int Depth, string Kind, string Label, IReadOnlyList<IWorkflowNodeViewModel> Nodes);

public static class CompiledOutline
{
    public static IReadOnlyList<CompiledOutlineRow> Of(CompiledGraph graph);
}
```

A compiled graph is already a view model — segments in observable collections — so a nested list can bind it directly. `CompiledOutline.Of` exists for the other shape: one flat, virtualizable list that shows the whole structure at once, computed once because a graph is frozen after compilation.

| Row field | Meaning |
|---|---|
| `Depth` | Nesting depth; `0` at the graph's own entries — what a list view indents by. |
| `Kind` | `"Execute"` (a `ChainSegment`), `"Branch"` (a `BranchSegment`), `"Parallel"` (a `ParallelSegment`), plus `"Option"` / `"Terminal"` for a branch's options. |
| `Label` | A compact description: the chain's nodes joined by `→`, or the router and its keys. |
| `Nodes` | The nodes this row names, in order. Empty for a row that names none. |

**Example (Demo / verified run):** for a compiled `Ticker → Bias → Printer` chain, `CompiledOutline.Of` yields exactly one row:

```text
Execute | TickerNode → BiasNode → PrinterNode
```

**Notes:** the vocabulary (`Execute` / `Branch` / `Parallel`) is the same one the Agent's projection of a compiled graph uses, so the two do not drift apart. The demo binds `CompiledOutline.Of` to its tree view (`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`), and the Avalonia host indents by `Depth` (`Examples/Workflow/Avalonia/Demo/Views/Workflow/DepthIndentConverter.cs`).
