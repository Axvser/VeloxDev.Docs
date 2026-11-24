# Retry and redirect

A node that throws is a failed drive; a node that calls `Error` is asking the run to go somewhere else. These are different levels, and the engine gives the host one hook for each: a retry policy for throws, `IRedirectable` for the node's own fallback decision. An error sink records both as data, and a compensator is told what the failed run already did.

This page continues from [Execute a graph](../00_execute-a-graph/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- A compiled graph and a node helper; the same `StepHelper` from the previous page.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Retry a thrown failure

Configure the policy on the session; no node change is needed.

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 10),
};
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
```

- **Only thrown exceptions are retried.** A node that calls `Error`/`Warn` is making a deliberate control-flow request, not a failure to try again.
- `RetryNumber` starts at `1`; `maxAttempts` includes the first try (`3` means try, retry, retry).
- A retry is **not** a new attempt: `Attempt` counts passes over the graph and does not move; the retry number is the policy's own.
- Cancellation is never retried. A policy that throws is treated as "do not retry".

**Expected result:** a node that throws twice and succeeds on the third drive ends the run `Completed`, with `Attempt == 1` and the final data from the downstream node.

## 4. Redirect with `IRedirectable`

The redirect decision belongs to the node. Implement `IRedirectable` on the node class (a subclass of your generated node is enough), then report the failure and name an upstream node.

```csharp
public partial class RedirectNode : StepNode, IRedirectable
{
    public Func<IRuntimeContext, INodeComponent?>? Redirect { get; set; }

    public Task<INodeComponent?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)
        => Task.FromResult(Redirect?.Invoke(context));
}
```

```csharp
b.Handler = async (ctx, ct) =>
{
    await ((IRuntimeContext)ctx).ErrorAsync("only 1 sample; run again");
    return null;
};
b.Redirect = _ => a;   // a is upstream
```

The pass ends at the requesting node; the engine maps the target to its compile order and starts a new pass, skipping every node before it. A router at or before the target is not driven again — only re-asked for its route key. The redirect cap is 50.

A returned node must be an **upstream compiled node**. A node's invalid answer is logged and ignored (the flow carries on); a host policy's invalid answer ends the flow, because a host that tried to place the run and named something impossible has a bug.

**Expected result:** `Attempt == 2`, `b` is driven twice, and the run ends `Completed` with `B-fixed`.

## 5. Record and compensate failures

`IExecutionErrorSink` receives failures as records (`ExecutionError`: phase, node, message, exception, attempt, order, level), not as log lines.

```csharp
ErrorSink = new DelegateExecutionErrorSink(e => errors.Add($"{e.Level}:{e.Message}")),
```

A retried-and-recovered node produces **no sink record**: the engine reports a failure when it gives up (or a node reports one itself), not on each retry.

`IExecutionCompensation` is called only when the run ends `Failed` or `Cancelled`, once per node the run registered, **most recent first**. The engine rolls nothing back itself; a node's effects are the host's to undo.

```csharp
Compensation = new DelegateExecutionCompensation(
    c => compensated.Add($"{((StepNode)c.Node).Title}:{c.Output ?? "null"}")),
```

One behaviour to know in 12.3.0: a node that **threw** is registered too, with a `null` output, so the compensator sees it as well as the successes. Filter on `Output` if you only want to undo nodes that produced something.

**Expected result:** the failed run reports `outcome=Failed` and the compensator collects `bad:null` and then `ok:OK`.

## 6. Verification

```powershell
dotnet run
```

Expected output:

```text
[retry] status=Completed attemptsOfFlaky=3 data=C(ok)
[retry] observed=RunStarted,NodeStarted,NodeSucceeded,NodeStarted,NodeFailed,NodeRetried,NodeStarted,NodeFailed,NodeRetried,NodeStarted,NodeSucceeded,NodeStarted,NodeSucceeded,RunEnded
[retry] sinkRecords=0
[redirect] status=Completed attempt=2 bDrives=2 data=B-fixed
[redirect] logs:
  01. StepNode
  02. drive a
  03. RedirectNode
  04. drive b
  05. [Error] only 1 sample; run again
  06. Redirecting to compile state #0 (skipping prior nodes, re-executing).
  07. StepNode
  08. drive a
  09. RedirectNode
  10. drive b
[compensation] status=Stopped outcome=Failed compensated=[bad:null,ok:OK]
```

## 7. Complete code

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Runtime.Failures;

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

/// <summary>A node that can decide to fall back to an upstream node after a failure.</summary>
public partial class RedirectNode : StepNode, IRedirectable
{
    public RedirectNode(string title) : base(title) { }
    public Func<IRuntimeContext, INodeComponent?>? Redirect { get; set; }

    public Task<INodeComponent?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)
        => Task.FromResult(Redirect?.Invoke(context));
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
        await Retry();
        await Redirect();
        await Compensation();
    }

    private static async Task Retry()
    {
        var tree = new DemoTree();
        var a = new StepNode("a") { Handler = (_, _) => Task.FromResult<object?>("A") };
        var flaky = new StepNode("flaky");
        var failures = 0;
        flaky.Handler = (_, _) => ++failures < 3
            ? throw new InvalidOperationException("transient")
            : Task.FromResult<object?>("ok");
        var c = new StepNode("c") { Handler = (ctx, _) => Task.FromResult<object?>($"C({ctx.Data})") };
        foreach (var n in new INodeComponent[] { a, flaky, c }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, flaky.Input);
        Wire(tree, flaky.Output, c.Input);

        var observations = new List<ExecutionObservationKind>();
        var errors = new List<string>();
        var session = new RuntimeContext
        {
            Data = "seed",
            RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 10),
            Observer = new DelegateExecutionObserver(o => observations.Add(o.Kind)),
            ErrorSink = new DelegateExecutionErrorSink(e => errors.Add($"{e.Level}:{e.Message}")),
        };

        await new RuntimeEngine().RunAsync(await Compile(a), session, CancellationToken.None);
        Console.WriteLine($"[retry] status={session.Status} attemptsOfFlaky={failures} data={session.Data}");
        Console.WriteLine($"[retry] observed={string.Join(",", observations)}");
        Console.WriteLine($"[retry] sinkRecords={errors.Count}");
    }

    private static async Task Redirect()
    {
        var tree = new DemoTree();
        var a = new StepNode("a") { Handler = (_, _) => Task.FromResult<object?>("A") };
        var b = new RedirectNode("b");
        var passes = 0;
        b.Handler = async (ctx, ct) =>
        {
            passes++;
            if (passes == 1)
            {
                await ((IRuntimeContext)ctx).ErrorAsync("only 1 sample; run again");
                return null;
            }
            return "B-fixed";
        };
        b.Redirect = _ => a;
        foreach (var n in new INodeComponent[] { a, b }) tree.GetHelper().CreateNode(n);
        Wire(tree, a.Output, b.Input);

        var session = new RuntimeContext { Data = "seed" };
        await new RuntimeEngine().RunAsync(await Compile(a), session, CancellationToken.None);
        Console.WriteLine($"[redirect] status={session.Status} attempt={session.Attempt} bDrives={passes} data={session.Data}");
        Console.WriteLine($"[redirect] logs:\n  {string.Join("\n  ", session.Logs)}");
    }

    private static async Task Compensation()
    {
        var tree = new DemoTree();
        var ok = new StepNode("ok") { Handler = (_, _) => Task.FromResult<object?>("OK") };
        var bad = new StepNode("bad")
        {
            Handler = (_, _) => throw new InvalidOperationException("delivery failed"),
        };
        foreach (var n in new INodeComponent[] { ok, bad }) tree.GetHelper().CreateNode(n);
        Wire(tree, ok.Output, bad.Input);

        var compensated = new List<string>();
        var session = new RuntimeContext
        {
            Data = "seed",
            Compensation = new DelegateExecutionCompensation(
                c => compensated.Add($"{((StepNode)c.Node).Title}:{c.Output ?? "null"}")),
        };
        await new RuntimeEngine().RunAsync(await Compile(ok), session, CancellationToken.None);
        Console.WriteLine($"[compensation] status={session.Status} outcome={session.Outcome} compensated=[{string.Join(",", compensated)}]");
    }
}
```

## 8. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
