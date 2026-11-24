# 重试与重定向

节点抛出异常是一次失败的驱动；节点调用 `Error` 则是要求这次运行改道。两者层级不同，引擎为宿主各提供一个钩子：重试策略处理抛出，`IRedirectable` 处理节点自己的回退决定。错误接收器把两者记成数据，补偿器则被告知失败的运行已经做过什么。

本页接着[执行编译图](../00_执行编译图/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 一张编译图和一个节点 Helper；与上一页的 `StepHelper` 相同。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 重试抛出的失败

在会话上配置策略，节点无需改动。

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 10),
};
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
```

- **只有抛出的异常会被重试。** 调用 `Error`/`Warn` 的节点是在做有意的控制流请求，不是等待重试的失败。
- `RetryNumber` 从 `1` 开始；`maxAttempts` 包含第一次尝试（`3` 表示尝试、重试、再重试）。
- 重试**不是**新的一趟：`Attempt` 统计过图趟数，不会变化；重试编号是策略自己的。
- 取消从不重试。策略自身抛出异常按「不再重试」处理。

**预期结果：** 一个抛出两次、第三次成功的节点最终使运行 `Completed`，`Attempt == 1`，最终数据来自下游节点。

## 4. 用 `IRedirectable` 重定向

重定向决定权属于节点。在节点类（生成节点的子类即可）上实现 `IRedirectable`，报告失败并指定一个上游节点。

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
b.Redirect = _ => a;   // a 在上游
```

本趟在提出请求的节点处结束；引擎把目标映射为它的编译序号，然后开始新的一趟，跳过目标之前的所有节点。位于目标处或之前的路由器不会被再次驱动——只会重新询问它的路由键。重定向上限为 50 次。

返回的节点必须是**上游的已编译节点**。节点的非法回答会被记录并忽略（流程继续）；宿主策略的非法回答会结束流程，因为一个试图安排运行却给出了不可能目标的宿主存在 bug。

**预期结果：** `Attempt == 2`，`b` 被驱动两次，运行以 `Completed` 和 `B-fixed` 结束。

## 5. 记录并补偿失败

`IExecutionErrorSink` 收到的是记录（`ExecutionError`：阶段、节点、消息、异常、趟数、序号、级别），而不是日志行。

```csharp
ErrorSink = new DelegateExecutionErrorSink(e => errors.Add($"{e.Level}:{e.Message}")),
```

被重试并最终恢复的节点**不会产生接收器记录**：引擎在放弃时（或节点自己报告时）才上报失败，而不是每次重试都上报。

`IExecutionCompensation` 只在运行以 `Failed` 或 `Cancelled` 结束时调用，按运行登记过的节点逐个回调，**最近执行的在前**。引擎自己不做任何回滚；节点的副作用由宿主决定如何撤销。

```csharp
Compensation = new DelegateExecutionCompensation(
    c => compensated.Add($"{((StepNode)c.Node).Title}:{c.Output ?? "null"}")),
```

12.3.0 有一个行为需要知道：**抛出异常的节点也会被登记**，输出为 `null`，因此补偿器既会看到成功节点，也会看到它。若只想撤销真正产出过东西的节点，请按 `Output` 过滤。

**预期结果：** 失败的运行报告 `outcome=Failed`，补偿器依次收到 `bad:null` 与 `ok:OK`。

## 6. 验证

```powershell
dotnet run
```

预期输出：

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

## 7. 完整代码

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

## 8. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
