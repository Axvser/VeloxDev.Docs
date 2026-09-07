# Workflow System — Compile a Graph (Root) and Run It

The compile entry point is the single method `CompilerViewModel.CompileAsync(node, CompileRole role, ct)`. With `CompileRole.Root` the node is a *starter*: the compiler walks downstream along `Targets` and decomposes the reachable sub-graph into **one** acyclic `CompiledGraph`, which it also stores in `CompilerViewModel.Graphs`. See `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs` and `CompileRole.cs`.

## 1. Compile forward from the controller node

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.WorkflowSystem;

public static class Runner
{
    public static async Task RunForwardAsync(QuickTree tree)
    {
        var ticker = tree.Nodes.OfType<TickerNode>().Single();
        var bias = tree.Nodes.OfType<BiasNode>().Single();
        var printer = tree.Nodes.OfType<PrinterNode>().Single();

        var compiler = new CompilerViewModel();
        IReadOnlyList<CompiledGraph> graphs =
            await compiler.CompileAsync(ticker, CompileRole.Root, CancellationToken.None);
        CompiledGraph graph = graphs[0];
    }
}
```

`CompileAsync` requires an `IWorkflowNodeViewModel` (it throws an `ArgumentException` otherwise) and returns `IReadOnlyList<CompiledGraph>`; `compiler.Graphs` mirrors the same result for UI binding.

**Expected result:** `graph.Entries.Count == 1` — the linear `Ticker → Bias → Printer` chain compiles to a single segment. Every node implementing `ICompileTimeAware` was injected with its compile identity: `ticker.CompileContext!.Order == 0`, `bias.CompileContext!.Order == 1`, `printer.CompileContext!.Order == 2`.

## 2. What a CompiledGraph is made of

`CompiledGraph.Entries` is an ordered `ObservableCollection<CompileSegment>`. The three concrete segments (`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Model/`) are:

| Segment | Meaning | Emitted for |
|---|---|---|
| `ChainSegment` | an ordered linear run of nodes | a single-input / single-output line (our `Ticker → Bias → Printer`) |
| `BranchSegment` | one router node + its `BranchOption`s | a node implementing `ICompileTimeRouter` |
| `ParallelSegment` | a fan-out group of child `CompiledGraph`s | one route key / plain output that feeds several downstream targets, or several producers joining into one node |

A router (`ICompileTimeRouter`) declares its branch structure at compile time with `GetRouteTable()` (key → downstream nodes) and re-selects at runtime with `ResolveRouteKey(payload)`; `RouterCompileMode.Static` locks the currently selected branch into the graph, `RouterCompileMode.Dynamic` keeps every branch alive. Branch segments nest child graphs, so a compiled graph is a tree of segments. The graph is acyclic and immutable — it *describes* possible executions; which branch actually runs is decided at runtime.

**Expected result:** for this linear graph, `graph.Entries[0] is ChainSegment` whose `Nodes` holds the three node instances in order.

## 3. Run the compiled graph

```csharp
var context = new RuntimeContext();
await new RuntimeEngine().RunAsync(graph, context, CancellationToken.None);

Console.WriteLine(context.Status);        // Completed
Console.WriteLine(context.Data);          // tick->bias->print
foreach (var line in context.Logs) Console.WriteLine(line);
```

`RuntimeEngine` (`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`) drives each segment: a `ChainSegment` drives its nodes one by one, a `BranchSegment` drives the router then the selected sub-graph, a `ParallelSegment` executes its branches in order. Each node is driven through its helper's `ReceiveAsync` with the *same* `RuntimeContext` session (nodes implementing `IRuntimeAware` also get the session injected). The node's return value is written back to `context.Data`, so the next node in the chain receives the previous node's output — which is exactly why `Bias` sees `"tick"` and `Printer` sees `"tick->bias"`.

**Expected result:** `context.Status == "Completed"`, `context.Data == "tick->bias->print"`, `context.Attempt == 1`, and `context.IsRunning` is `false` when `RunAsync` returns. Cancelling the token (or a non-redirectable node error) yields `Status == "Stopped"` instead.

## 4. The three execution entry points

The compiled run is only one of three ways to execute nodes (see the `EntrySemanticsTests` in `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`).

**Node level.** Call a node's receive path directly:

```csharp
var result = await ticker.GetHelper().ReceiveAsync(
    new TaskContext("hello"), CancellationToken.None);
```

`TaskContext` (`Src/Core/VeloxDev.Core/WorkflowSystem/TaskContext.cs`) is the read-only `ITaskContext` carrier `(Data, Sender, Receiver)`.

**Edge level.** Broadcast a payload along every valid outgoing link; each accepted edge delivers a `TaskContext` to the downstream node's `ReceiveCommand` (`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs`):

```csharp
using VeloxDev.WorkflowSystem.StandardEx;
await ticker.StandardBroadcastAsync("hello", CancellationToken.None);
```

An edge whose `AccessAsync` rejects the payload is treated as unconnected and skipped.

**Chain level (compiled).** The engine in step 3 owns downstream dispatch: it drives nodes only via `Helper.ReceiveAsync` and never triggers a node's `ReceiveCommand` / `BroadcastCommand`.

Go to [Compile a result (Terminal)](../05_terminal-compile/index.md).
