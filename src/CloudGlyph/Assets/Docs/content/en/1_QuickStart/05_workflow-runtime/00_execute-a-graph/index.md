# Execute a graph

The runtime engine drives a compiled graph segment by segment. Chain nodes run in order and pass their return value to the next node; a fan-out starts its branches from the same source payload; a join receives an `IGroupData` keyed by the upstream node. The session records the outcome, the attempt and the log.

This page continues from [Root compilation](../../04_workflow-compiler/00_root-compilation/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- A compiled graph: this page compiles one from a tree, but any `CompiledGraph` works.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Give a node its computation

The generated node forwards `ReceiveCommand` to its helper's `ReceiveAsync`. Write a helper that derives from `NodeHelper<TNode>` and override that method; install it through `[WorkflowBuilder.Node<StepHelper>]`.

```csharp
public class StepHelper : NodeHelper<StepNode>
{
    public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        var node = Component!;
        var runtime = context as IRuntimeContext;
        runtime?.Log($"drive {node.Title} attempt={runtime.Attempt}");
        return await Task.FromResult(node.Handler?.Invoke(context, ct));
    }
}
```

`Component` is the node the helper is installed on. `ReceiveAsync` is the **single execution entry**: the compiled engine calls it directly and takes the return value as the next node's payload. It does not broadcast — the engine owns dispatch.

**Expected result:** each driven node writes one `drive …` line after the engine's own type-name line.

## 4. Compile and run

```csharp
var graph = (await new CompilerViewModel().CompileAsync(a, CompileRole.Root))[0];
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
```

`RuntimeContext` is both the `IRuntimeContext` the engine writes and the `ITaskContext` each node receives. `Data` is the seed for the first node.

**Expected result:** `session.Status == "Completed"`, `session.Attempt == 1`, and `session.Data` is the last node's output.

## 5. Data flow

- The first node receives `session.Data` (the seed).
- After a node returns, the engine stores the value in `session.Data`; the next chain node receives it as `context.Data`.
- `context.Data` is read-only (`ITaskContext`); the engine and the session own the writes. `IRuntimeContext.Data` adds the setter for hosts.
- `AttachRuntimeContext` (optional `IRuntimeAware`) is only a notification of that same session — implementing it changes no behaviour.

**Expected result:** with handlers `a → "A"`, `b → $"B({ctx.Data})"`, `c → $"C({ctx.Data})"`, the final value is `C(B(A))`.

## 6. Fan-out and joins

A fan-out node with several valid targets compiles to a `ParallelSegment`. Every branch starts from the **same** source payload and cannot see a sibling's output. The branches run concurrently as interleaved async operations, not on separate threads.

When the branches converge on one node, the compiler registers that join's input sources. Before driving it, the engine replaces `Data` with a `GroupData`: a read-only dictionary keyed by the **source node reference**.

```csharp
join.Handler = (ctx, _) =>
{
    var group = (IGroupData)ctx.Data!;
    var parts = group.Select(kv => $"{((StepNode)kv.Key).Title}={kv.Value}");
    return $"JOIN[{string.Join(",", parts)}]";
};
```

**Expected result:** `JOIN[a=AV,b=BV]`. An upstream that was not driven this pass is absent from the dictionary, so `TryGetValue` returns `false` rather than a stale value.

## 7. Outcome, attempt and logs

- `Status` is `Idle`, `Running`, `Paused`, `Completed` or `Stopped`.
- `Outcome` resolves the ambiguous `Stopped`: `Failed` when `EndedWithError` is set, `Cancelled` when the host's token ended it, `Completed` otherwise.
- `Attempt` counts passes over the graph. A redirect increments it; a retry does not.
- `Logs` receives the engine's type-name lines and every `Log`/`Warn`/`Error`. `SnapshotLogs()` is the safe way to read it while a run is appending.

**Expected result:** the chain run logs six lines (three type names, three node lines), and the session ends `Completed` with `Attempt == 1`.

## 8. Verification

```powershell
dotnet run
```

Expected output:

```text
[chain] status=Completed outcome=Completed attempt=1
[chain] final data=C(B(A))
[chain] logs:
  01. StepNode
  02. drive a attempt=1
  03. StepNode
  04. drive b attempt=1
  05. StepNode
  06. drive c attempt=1
[join] status=Completed data=JOIN[a=AV,b=BV]
[join] segments=ChainSegment,ParallelSegment,ChainSegment
```

## 9. Complete code

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Runtime.Execute;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<StepHelper>]
public partial class StepNode
{
    public StepNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Step";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
    public Func<ITaskContext, CancellationToken, object?>? Handler { get; set; }
}

public class StepHelper : NodeHelper<StepNode>
{
    public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        var node = Component!;
        var runtime = context as IRuntimeContext;
        runtime?.Log($"drive {node.Title} attempt={runtime.Attempt}");
        return await Task.FromResult(node.Handler?.Invoke(context, ct));
    }
}

public static class Program
{
    private static void Wire(DemoTree tree, ISlotComponent from, ISlotComponent to)
    {
        tree.GetHelper().SendConnection(from);
        tree.GetHelper().ReceiveConnection(to);
    }

    private static async Task<CompiledGraph> Compile(INodeComponent start)
        => (await new CompilerViewModel().CompileAsync(start, CompileRole.Root))[0];

    public static async Task Main()
    {
        await Chain();
        await FanOutJoin();
    }

    private static async Task Chain()
    {
        var tree = new DemoTree();
        var a = new StepNode("a") { Handler = (_, _) => "A" };
        var b = new StepNode("b") { Handler = (ctx, _) => $"B({ctx.Data})" };
        var c = new StepNode("c") { Handler = (ctx, _) => $"C({ctx.Data})" };
        foreach (var n in new INodeComponent[] { a, b, c }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, b.Input);
        Wire(tree, b.Output, c.Input);

        var graph = await Compile(a);
        var session = new RuntimeContext { Data = "seed" };
        await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);

        Console.WriteLine($"[chain] status={session.Status} outcome={session.Outcome} attempt={session.Attempt}");
        Console.WriteLine($"[chain] final data={session.Data}");
        Console.WriteLine($"[chain] logs:\n  {string.Join("\n  ", session.Logs)}");
    }

    private static async Task FanOutJoin()
    {
        var tree = new DemoTree();
        var p = new StepNode("p") { Handler = (_, _) => "SRC" };
        var a = new StepNode("a") { Handler = (_, _) => "AV" };
        var b = new StepNode("b") { Handler = (_, _) => "BV" };
        var join = new StepNode("join")
        {
            Handler = (ctx, _) =>
            {
                var group = (IGroupData)ctx.Data!;
                var parts = group.Select(kv => $"{((StepNode)kv.Key).Title}={kv.Value}");
                return $"JOIN[{string.Join(",", parts)}]";
            },
        };
        foreach (var n in new INodeComponent[] { p, a, b, join }) tree.GetHelper().CreateNode(n);
        p.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
        join.Input.SetChannelCommand.Execute(SlotChannel.MultipleSources);
        Wire(tree, p.Output, a.Input);
        Wire(tree, p.Output, b.Input);
        Wire(tree, a.Output, join.Input);
        Wire(tree, b.Output, join.Input);

        var graph = await Compile(p);
        var session = new RuntimeContext { Data = "seed" };
        await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
        Console.WriteLine($"[join] status={session.Status} data={session.Data}");
        Console.WriteLine($"[join] segments={string.Join(",", graph.Entries.Select(e => e.GetType().Name))}");
    }
}
```

## 10. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
