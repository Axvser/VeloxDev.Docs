# Workflow System — Parallel Fan-Out, Its Concurrency Cap, and the Compiled Outline

When one node feeds several downstream targets, the compiler wraps the branches in a `ParallelSegment` and the engine runs them **concurrently**. `MaxParallelBranches` bounds how many are in flight at once. `CompiledOutline` flattens any compiled graph into one bindable list.

## 1. Add a fan-out to the graph

A plain node whose output slot accepts several connections fans out. Create `FanOutNodes.cs`:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

[WorkflowBuilder.Node<SourceHelper>(workSemaphore: 1)]
public partial class SourceNode : ICompileTimeAware
{
    public SourceNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class SourceHelper : NodeHelper<SourceNode>
{
    public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        => Task.FromResult<object?>("SRC");
}

// The two branches record when they start and end, so overlapping can be measured.
public static class BranchClock
{
    public static readonly List<(int Index, int Tick)> Starts = [];
    public static readonly List<(int Index, int Tick)> Ends = [];
}

[WorkflowBuilder.Node<LeftHelper>(workSemaphore: 1)]
public partial class LeftNode : ICompileTimeAware
{
    public LeftNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class LeftHelper : NodeHelper<LeftNode>
{
    public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        BranchClock.Starts.Add((0, Environment.TickCount));
        await Task.Delay(120, ct);
        BranchClock.Ends.Add((0, Environment.TickCount));
        return Task.FromResult<object?>("L");
    }
}

[WorkflowBuilder.Node<RightHelper>(workSemaphore: 1)]
public partial class RightNode : ICompileTimeAware
{
    public RightNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class RightHelper : NodeHelper<RightNode>
{
    public override async Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        BranchClock.Starts.Add((1, Environment.TickCount));
        await Task.Delay(120, ct);
        BranchClock.Ends.Add((1, Environment.TickCount));
        return Task.FromResult<object?>("R");
    }
}
```

**Expected result:** the project compiles.

## 2. Build and compile the fan-out

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.WorkflowSystem;

var tree = new QuickTree();
var helper = tree.GetHelper();
var source = new SourceNode { Anchor = new Anchor(0, 0, 0) };
var left = new LeftNode { Anchor = new Anchor(200, 0, 0) };
var right = new RightNode { Anchor = new Anchor(400, 0, 0) };
helper.CreateNode(source);
helper.CreateNode(left);
helper.CreateNode(right);

source.OutputSlot.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
left.InputSlot.SetChannelCommand.Execute(SlotChannel.OneSource);
right.InputSlot.SetChannelCommand.Execute(SlotChannel.OneSource);

helper.SendConnection(source.OutputSlot!);
helper.ReceiveConnection(left.InputSlot!);
helper.SendConnection(source.OutputSlot!);
helper.ReceiveConnection(right.InputSlot!);

var graph = (await new CompilerViewModel().CompileAsync(
    source, CompileRole.Root, CancellationToken.None))[0];
Console.WriteLine(string.Join(", ", graph.Entries.Select(e => e.GetType().Name)));
```

**Expected result:** `ChainSegment, ParallelSegment` — the source compiles into a one-node chain, and its two targets become a fan-out group. The `MultipleTargets` channel is what lets the source's output slot accept two connections; `OneSource` on each input is enough for one incoming edge.

## 3. Branches run concurrently by default

```csharp
BranchClock.Starts.Clear(); BranchClock.Ends.Clear();
var uncapped = new RuntimeContext();
await new RuntimeEngine().RunAsync(graph, uncapped, CancellationToken.None);

var s0 = BranchClock.Starts.First(s => s.Index == 0).Tick;
var s1 = BranchClock.Starts.First(s => s.Index == 1).Tick;
var e0 = BranchClock.Ends.First(e => e.Index == 0).Tick;
var e1 = BranchClock.Ends.First(e => e.Index == 1).Tick;
Console.WriteLine($"overlap={s0 < e1 && s1 < e0}");
```

**Expected result:** `overlap=True` — both branches were in flight at the same time. Every branch starts from the **fan-out source's payload**, never from a sibling's output.

**Notes:** this is interleaved async work on the caller's `SynchronizationContext`, not thread parallelism: each branch starts on the caller's context and every `await` inside it yields to its siblings, so I/O-bound branches overlap while a branch that burns CPU still occupies the thread in turn. That is deliberate — moving node bodies to the thread pool would break the contract that components are UI-bound.

## 4. Cap the group

```csharp
BranchClock.Starts.Clear(); BranchClock.Ends.Clear();
var capped = new RuntimeContext { MaxParallelBranches = 1 };
await new RuntimeEngine().RunAsync(graph, capped, CancellationToken.None);

var t0 = BranchClock.Starts.First(s => s.Index == 0).Tick;
var t1 = BranchClock.Starts.First(s => s.Index == 1).Tick;
var u0 = BranchClock.Ends.First(e => e.Index == 0).Tick;
var u1 = BranchClock.Ends.First(e => e.Index == 1).Tick;
Console.WriteLine($"overlap={t0 < u1 && t1 < u0}");
```

**Expected result:** `overlap=False` — a cap of one lets a branch finish before the next starts.

**Notes:** the cap is **per group**, not per run, and it is read off the concrete `RuntimeContext` (`ExecutionGateTests` and `ParallelExecutionTests` both pin this). `null` (the default) means no cap. Set it when the branches are heavy — each spawning a process or holding a large buffer — and the machine would rather work through them in waves. **No demo sets it**; the contract is pinned by `ParallelExecutionTests.MaxParallelBranches_SerialisesTheGroupWhenSetToOne`.

Two more fan-out rules worth knowing: **a terminal branch hit inside any branch ends the whole run**, and when several branches request a redirect the **first in branch order** wins while the others are logged and ignored (by order, not by wall clock, so a run stays reproducible).

## 5. Flatten the graph into an outline

```csharp
foreach (var row in CompiledOutline.Of(rootGraph))          // rootGraph: the linear chain
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind} | {row.Label}");
```

**Expected result:**

```text
Execute | TickerNode → BiasNode → PrinterNode
```

Each row carries `Depth` (indent by it), `Kind` (`Execute` / `Branch` / `Parallel`, plus `Option` / `Terminal` for a branch's options), `Label` and the `Nodes` it names. For the fan-out graph above you get a `Parallel` row at depth 0 with one `Execute` row per branch beneath it.

**Notes:** a compiled graph is already a view model, so a nested list can bind it directly; `CompiledOutline` exists for the other shape — one flat, virtualizable list that shows the whole structure at once.

## 6. Where this lives in the real repository

`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` builds the outline for its tree view, and the Avalonia host indents by `Depth` (`Examples/Workflow/Avalonia/Demo/Views/Workflow/DepthIndentConverter.cs`). The demo's `WorkflowDemoSession` compiles a graph with several fan-outs (the `[Stats, Dist, Anomaly]` group feeding a join).

Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ParallelExecutionTests.cs` and `CompiledOutlineTests.cs`.

Go to `Verify & complete code`.
