# Pause, observe and checkpoint

A run can be held between nodes, watched as a timeline, and written down so a later run picks it up. All three are optional and live on `RuntimeContext`; with none configured the run behaves exactly as before.

This page continues from [Execute a graph](../00_execute-a-graph/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- A compiled graph and a node helper; the same `StepHelper` from the previous pages.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Pause between nodes

`IExecutionGate` is awaited **before each node**, never inside one. `ManualExecutionGate` is the hand-operated implementation: `Pause()` holds the run at the next node boundary, `Resume()` lets it go from any thread.

```csharp
var gate = new ManualExecutionGate();
var session = new RuntimeContext { Data = "seed", ExecutionGate = gate };
var run = new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);

gate.Resume();   // or call Pause() from inside a node handler
```

While the gate holds, `Status` is `Paused` and `IsRunning` stays `true` — a paused run is not a stopped one. A node already being driven runs to completion, so a pause cannot split an edit. Cancelling the run's token while paused ends it (`Status == "Stopped"`, outcome `Cancelled`) instead of leaving it parked.

**Expected result:** while held, `status=Paused running=True completed=False`; after `Resume`, the run finishes `Completed`.

## 4. Observe the timeline

`IExecutionObserver` receives one `ExecutionObservation` per step: `RunStarted`, `NodeStarted`, `NodeSucceeded`, `NodeFailed`, `NodeRetried`, `BranchStarted`, `RunEnded`.

```csharp
Observer = new DelegateExecutionObserver(o => observed.Add(o.Kind)),
```

The observation carries the node (or `null` for run/branch-level events), a free-form detail, the pass `Attempt`, and the elapsed time. A broken observer never changes the run: an exception is logged and the drive continues.

**Expected result:** for a two-node chain that pauses and resumes, the kinds are `RunStarted, NodeStarted, NodeSucceeded, NodeStarted, NodeSucceeded, RunEnded`.

## 5. Divert the log to a file

`ILogWriter` receives every already-formatted line — the engine's and every node's. `TextWriterLogWriter.For(path)` opens a file for append and owns the stream.

```csharp
var writer = TextWriterLogWriter.For(path);
var session = new RuntimeContext { Data = "seed", LogWriter = writer };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
writer.Dispose();   // whoever opened the stream closes it
```

- Lines arrive in the order they happened, and `Logs` receives the same lines in the same order — the two views are comparable line for line.
- Writes happen on the thread driving the run. A synchronous file write therefore puts that IO on that thread; queue and drain elsewhere if that matters.
- A writer that throws is reported through `RuntimeContext.LogWriteFailed`; the line is still kept in `Logs` and the run continues.
- `MaxRetainedLogs` bounds the in-memory view while the writer keeps everything. It is unbounded by default on purpose.

**Expected result:** the file and `Logs` have the same line count and the same first line (`01. StepNode`).

## 6. Checkpoint and resume

An `IExecutionCheckpointStore` is written after each node succeeds. The engine hands over `RuntimeContext.Snapshot()`; a store keeps the latest state, not a history.

```csharp
var store = new InMemoryCheckpointStore();
var first = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, first, CancellationToken.None);

var place = await store.LoadAsync(CancellationToken.None);
var second = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, second, CancellationToken.None, place);
```

- `ExecutionCheckpoint.Shape` is the graph's node-key fingerprint. Resuming onto a graph whose shape differs throws `InvalidOperationException` before the session is touched.
- Nodes the checkpoint records as done are not driven again. A checkpoint taken after a full run therefore resumes with zero drives; a checkpoint taken after an interruption resumes from that point.
- `ExecutionCheckpoint.Rekey(checkpoint, graph)` re-files a checkpoint onto the same structure with new node identities (what a serialization round trip produces); it checks node count and node types, not identity.
- The store's `SaveAsync` may be called from two fan-out branches at once; a file-backed implementation must serialise its own writes.

**Expected result:** `shape=3 outputs=3`; the resumed run drives nothing, reports `C`, and ends `Completed`.

## 7. Verification

```powershell
dotnet run
```

Expected output:

```text
[gate] while held: status=Paused running=True completed=False
[gate] after resume: status=Completed data=B
[gate] observed=RunStarted,NodeStarted,NodeSucceeded,NodeStarted,NodeSucceeded,RunEnded
[log] inMemory=4 file=4 sameFirst=True
[checkpoint] saved shape=3 outputs=3 attempt=1
[checkpoint] resumed drives=0 output=C status=Completed
```

## 8. Complete code

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Runtime.Lifecycle;

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
    public Func<ITaskContext, CancellationToken, Task<object?>>? Handler { get; set; }
}

public class StepHelper : NodeHelper<StepNode>
{
    public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        var node = Component!;
        (context as IRuntimeContext)?.Log($"drive {node.Title}");
        return node.Handler is { } handler ? await handler(context, ct) : null;
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
        await GateAndObserve();
        await LogToFile();
        await Checkpoint();
    }

    private static async Task GateAndObserve()
    {
        var tree = new DemoTree();
        var gate = new ManualExecutionGate();
        var a = new StepNode("a");
        var b = new StepNode("b") { Handler = (_, _) => Task.FromResult<object?>("B") };
        var closed = new TaskCompletionSource<bool>();
        a.Handler = (_, _) =>
        {
            gate.Pause();
            closed.TrySetResult(true);
            return Task.FromResult<object?>("A");
        };
        foreach (var n in new INodeComponent[] { a, b }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, b.Input);

        var observed = new List<ExecutionObservationKind>();
        var session = new RuntimeContext
        {
            Data = "seed",
            ExecutionGate = gate,
            Observer = new DelegateExecutionObserver(o => observed.Add(o.Kind)),
        };
        var run = new RuntimeEngine().RunAsync(await Compile(a), session, CancellationToken.None);
        await closed.Task;
        await Task.Delay(100);
        Console.WriteLine($"[gate] while held: status={session.Status} running={session.IsRunning} completed={run.IsCompleted}");

        await Task.Run(gate.Resume);
        await run;
        Console.WriteLine($"[gate] after resume: status={session.Status} data={session.Data}");
        Console.WriteLine($"[gate] observed={string.Join(",", observed)}");
    }

    private static async Task LogToFile()
    {
        var path = Path.Combine(Path.GetTempPath(), $"velox-wiki-{Guid.NewGuid():N}.log");
        var tree = new DemoTree();
        var a = new StepNode("a") { Handler = (_, _) => Task.FromResult<object?>("A") };
        var b = new StepNode("b") { Handler = (_, _) => Task.FromResult<object?>("B") };
        foreach (var n in new INodeComponent[] { a, b }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, b.Input);

        var graph = await Compile(a);
        var writer = TextWriterLogWriter.For(path);
        var session = new RuntimeContext { Data = "seed", LogWriter = writer };
        await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
        writer.Dispose();

        var fileLines = File.ReadAllLines(path);
        Console.WriteLine($"[log] inMemory={session.Logs.Count} file={fileLines.Length} sameFirst={session.Logs[0] == fileLines[0]}");
    }

    private static async Task Checkpoint()
    {
        var tree = new DemoTree();
        var calls = new List<string>();
        var a = new StepNode("a");
        var b = new StepNode("b");
        var c = new StepNode("c");
        foreach (var (node, name) in new[] { (a, "a"), (b, "b"), (c, "c") })
            node.Handler = (_, _) => { calls.Add(name); return Task.FromResult<object?>(name.ToUpperInvariant()); };
        foreach (var n in new INodeComponent[] { a, b, c }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, b.Input);
        Wire(tree, b.Output, c.Input);

        var graph = await Compile(a);
        var store = new InMemoryCheckpointStore();
        var first = new RuntimeContext { Data = "seed", CheckpointStore = store };
        await new RuntimeEngine().RunAsync(graph, first, CancellationToken.None);

        var place = await store.LoadAsync(CancellationToken.None);
        Console.WriteLine($"[checkpoint] saved shape={place!.Shape.Count} outputs={place.Outputs.Count} attempt={place.Attempt}");

        calls.Clear();
        var second = new RuntimeContext { Data = "seed", CheckpointStore = store };
        await new RuntimeEngine().RunAsync(graph, second, CancellationToken.None, place);
        Console.WriteLine($"[checkpoint] resumed drives={calls.Count} output={second.Data} status={second.Status}");
    }
}
```

## 9. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
