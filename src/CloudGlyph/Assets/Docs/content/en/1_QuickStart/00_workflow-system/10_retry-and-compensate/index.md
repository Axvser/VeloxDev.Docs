# Workflow System — Retry a Failing Node and Compensate a Bad Run

Two capabilities about failure: a retry policy gives a node that **threw** another go, and a compensator is told what a run that ended badly already did so the host can undo it.

## 1. Add a node that fails the first two times

Create `FlakyNode.cs` in the `WorkflowQuickStart` project:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

[WorkflowBuilder.Node<FlakyHelper>(workSemaphore: 1)]
public partial class FlakyNode : ICompileTimeAware
{
    public FlakyNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class FlakyHelper : NodeHelper<FlakyNode>
{
    public static int Attempts;

    public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        Attempts++;
        if (Attempts < 3) throw new InvalidOperationException($"flaky #{Attempts}");
        return Task.FromResult<object?>("ok");
    }
}
```

**Expected result:** the project compiles. Without a retry policy this node would end the run on its first throw.

## 2. Attach a retry policy

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var tree = new QuickTree();
var helper = tree.GetHelper();
var flaky = new FlakyNode { Anchor = new Anchor(0, 0, 0) };
helper.CreateNode(flaky);

var graph = (await new CompilerViewModel().CompileAsync(
    flaky, CompileRole.Root, CancellationToken.None))[0];

var context = new RuntimeContext
{
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 1),
};

await new RuntimeEngine().RunAsync(graph, context, CancellationToken.None);
Console.WriteLine($"{context.Status} data={context.Data} drives={FlakyHelper.Attempts} attempt={context.Attempt}");
Console.WriteLine(string.Join(" | ", context.Logs));
```

**Expected result:**

```text
Completed data=ok drives=3 attempt=1
01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
```

Three drives, `data=ok`, and `attempt=1`: **a retry is not a pass over the graph.** Also note there is no `[Error]` line — an attempt that is going to be retried is not an error yet.

**Notes:** only **thrown exceptions** are retried. A node that calls `Error` / `ErrorAsync` is making a deliberate redirect request — control flow it asked for, not a failure to try again — so no policy is consulted. The node is re-driven from the **same input** it started with. Cancellation during the retry wait ends the run. A policy that always returns a delay retries forever: the run has no other cap, so use `NodeFailure.RetryNumber` to stop eventually.

## 3. Add a node that always fails

`BoomNode.cs`:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

[WorkflowBuilder.Node<BoomHelper>(workSemaphore: 1)]
public partial class BoomNode : ICompileTimeAware
{
    public BoomNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class BoomHelper : NodeHelper<BoomNode>
{
    public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        => throw new InvalidOperationException("boom");
}
```

**Expected result:** the project still compiles.

## 4. Attach a compensator

```csharp
var compensated = new List<string>();
var boom = new BoomNode { Anchor = new Anchor(0, 0, 0) };
var boomTree = new QuickTree();
boomTree.GetHelper().CreateNode(boom);
var boomGraph = (await new CompilerViewModel().CompileAsync(
    boom, CompileRole.Root, CancellationToken.None))[0];

var context = new RuntimeContext
{
    Compensation = new DelegateExecutionCompensation(c => compensated.Add(c.Node.GetType().Name)),
};

try
{
    await new RuntimeEngine().RunAsync(boomGraph, context, CancellationToken.None);
}
catch (InvalidOperationException) { }        // the node's own exception surfaces to the caller

Console.WriteLine($"{context.Status} {context.Outcome} currentOrder={context.CurrentOrder} reversed=[{string.Join(", ", compensated)}]");
```

**Expected result:**

```text
Stopped Failed currentOrder=-1 reversed=[BoomNode]
```

The run ended `Stopped` / `Failed`, the status code dropped to `-1` (absolute stop), and the compensator was handed the node that had succeeded before the failure — most recent first. Here there is only one.

**Notes:** **the engine does not roll anything back, and cannot.** A node's effects are its own — a property it wrote, a process it started, a file it left behind — and only the host knows which of those are reversible. The tree's undo stack is not a substitute: it records model-structure changes only, it is one flat stack with no run boundary, and it does not guarantee the chain completes.

A compensation is called **only** when the outcome is `Failed` or `Cancelled` — a completed run compensates nothing. A compensator that throws is logged (`[Compensation] …`) and the remaining nodes still run, because the original failure stays the headline. A node driven twice by a redirect appears **once**, at its most recent success.

## 5. Where this lives in the real repository

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, `ConfigureRun`:

```csharp
// The publish node's first delivery fails on purpose; this is what gets it through.
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
context.Compensation = new DelegateExecutionCompensation(
    c => Controller.RuntimeContext?.Log($"[Compensation] undo {NameOf(c.Node)} (attempt {c.Order})"));
```

Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionRetryTests.cs` (including `ANodeThatAsksForARedirect_IsNotRetried` and `CancellingDuringTheRetryWait_EndsTheRun`) and `ExecutionCompensationTests.cs`.

Go to `Checkpoints and log files`.
