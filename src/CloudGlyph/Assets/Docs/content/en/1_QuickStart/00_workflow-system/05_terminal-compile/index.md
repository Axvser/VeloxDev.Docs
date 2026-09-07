# Workflow System — Compile a Result (Terminal)

Sometimes you do not want to run a whole graph from a controller — you want the **value of one node** (a report, a computed number, a single output). Pass that node with `CompileRole.Terminal`: the compiler walks **backward along `Sources`** over valid edges, collects the node's *ancestor cone*, derives the cone's entry frontier automatically, and compiles only what is needed to produce that node. No explicit start node / controller is required. See `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs`.

## 1. Reverse-compile the result node

Target `BiasNode` (a middle node of the chain). Its cone is `{ Ticker, Bias }` and the compiled graph is the same shape as a forward run starting at `Ticker`, but it stops at `Bias` — `Printer` is outside the cone and is not compiled:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

public static async Task<RuntimeContext> RunResultAsync(QuickTree tree)
{
    var bias = tree.Nodes.OfType<BiasNode>().Single();

    var compiler = new CompilerViewModel();
    var graphs = await compiler.CompileAsync(bias, CompileRole.Terminal, CancellationToken.None);
    var graph = graphs[0];

    var result = new RuntimeContext { Target = bias };
    await new RuntimeEngine().RunAsync(graph, result, CancellationToken.None);

    Console.WriteLine(result.TargetReached);   // True
    Console.WriteLine(result.Status);          // Completed
    Console.WriteLine(result.Data);            // tick->bias   (NOT tick->bias->print)
    return result;
}
```

**Expected result:** the run stops after `Bias`; `result.Data` is `"tick->bias"` (the result node's own output), and because the node was actually driven, `result.TargetReached == true`. Set `RuntimeContext.Target` on any run — root or terminal — to have the engine track whether that node was driven.

## 2. Forward-consistent semantics on a cone

Terminal compilation does **not** flatten or guess branches. On the way to the target, routers keep their real `BranchSegment` semantics, but only the branch(es) whose targets lie inside the cone are compiled. If, at runtime, the router resolves a *sibling* branch (one not leading to the target), the flow simply ends before the target — exactly as forward semantics would behave. The target is never fabricated:

- If the selected branch reaches the target → the target runs and `RuntimeContext.TargetReached == true`.
- If the router selects a sibling branch → the target is not driven, `TargetReached == false`, and no value is invented for it (`Data` stays whatever the last driven node left).
- A cone whose independent producers do not funnel into one common join cannot be expressed (the compiler throws an informative `InvalidOperationException` rather than guessing).

These rules are pinned by `CompileToReverseTests` and `RuntimeEngineRunTests` in `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/` (e.g. `RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`). The real routing example to read is `EnumSelectorNodeViewModel` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`), whose dynamic `ResolveRouteKey` picks the branch from the data payload.

**Expected result:** reverse-compiling the demo's Enum Selector target keeps the router alive with only the in-cone branch in `BranchSegment.Options`.

## 3. The context hierarchy

Every payload that travels through nodes builds on a small hierarchy (all in `VeloxDev.WorkflowSystem` / `VeloxDev.Core.WorkflowSystem.CompilerEx`):

```text
IContext                 // object? Data  (real data at runtime, always null at compile time)
├── IAccessContext      // + IsCompilePhase, Sender, Receiver   (parameter of AccessAsync)
│   ├── ITaskContext    // ReceiveCommand → Helper.ReceiveAsync parameter (read-only)
│   └── ICompileContext // + Order / ChainIndex / Offset / InputNodes  (compile identity)
└── IRuntimeContext : ITaskContext
                        // runtime session: Uid / Logs / Status / Attempt / blackboard
                        // Set-TryGet / Target / TargetReached / writable Data
```

`RuntimeContext` is the concrete session you hand to `RuntimeEngine.RunAsync`. It is shared — one instance is injected into every node of a run — and it chains values: the engine writes each node's output back to `RuntimeContext.Data` for the next node. `Error()`/`Warn()` on the session request a redirect: a node implementing `IRedirectable` may fall back to an earlier compile state (its `ICompileContext.Order`), otherwise the run ends with status `Stopped` and `Order = -1`. Multi-input joins receive an `IGroupData` (a read-only dictionary of *source node → its output*) instead of a bare payload, so a join can read each upstream's result via `context.Data is IGroupData group` and `group.TryGetValue(sourceNode, out var v)`. Compiled graphs are acyclic; redirect is purely a runtime contract.

Go to [Serialize & rebuild the tree](../06_serialization/index.md).
