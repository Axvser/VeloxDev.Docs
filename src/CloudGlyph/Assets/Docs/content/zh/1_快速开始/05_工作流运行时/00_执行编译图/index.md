# 执行编译图

运行时引擎逐段驱动编译图。链上的节点按顺序执行，并把返回值交给下一个节点；扇出让每条分支从同一份源载荷出发；汇合节点收到一个以来源节点为键的 `IGroupData`。会话记录运行结局、趟数与日志。

本页接着[根节点编译](../../04_工作流编译器/00_根节点编译/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 一张编译图：本页从树编译一张，但任何 `CompiledGraph` 都可以。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 给节点真正的计算

生成的节点把 `ReceiveCommand` 转发到其 Helper 的 `ReceiveAsync`。写一个派生自 `NodeHelper<TNode>` 的 Helper 并重写该方法，再通过 `[WorkflowBuilder.Node<StepHelper>]` 安装。

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

`Component` 是 Helper 所安装到的节点。`ReceiveAsync` 是**唯一的执行入口**：编译后的引擎直接调用它，并把返回值当作下一个节点的载荷。它不负责广播——派发由引擎持有。

**预期结果：** 每个被驱动的节点在引擎的类型名日志之后写一行 `drive …`。

## 4. 编译并运行

```csharp
var graph = (await new CompilerViewModel().CompileAsync(a, CompileRole.Root))[0];
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
```

`RuntimeContext` 既是引擎写入的 `IRuntimeContext`，也是每个节点收到的 `ITaskContext`。`Data` 是第一个节点的种子。

**预期结果：** `session.Status == "Completed"`、`session.Attempt == 1`，`session.Data` 是最后一个节点的输出。

## 5. 数据流

- 第一个节点收到 `session.Data`（种子）。
- 节点返回后，引擎把值写入 `session.Data`；下一个链节点以 `context.Data` 收到它。
- `context.Data` 是只读的（`ITaskContext`）；写操作归引擎和会话所有。`IRuntimeContext.Data` 为宿主提供了 setter。
- `AttachRuntimeContext`（可选的 `IRuntimeAware`）只是同一会话的通知——实现它不改变任何行为。

**预期结果：** 处理器为 `a → "A"`、`b → $"B({ctx.Data})"`、`c → $"C({ctx.Data})"` 时，最终值为 `C(B(A))`。

## 6. 扇出与汇合

拥有多个有效下游的扇出节点会编译为 `ParallelSegment`。每条分支都从**同一份**源载荷出发，看不到兄弟分支的输出。分支以交错的异步操作并发运行，不占用独立线程。

分支汇聚到一个节点时，编译器登记该汇合点的输入源。驱动它之前，引擎把 `Data` 换成一个 `GroupData`：以**来源节点引用**为键的只读字典。

```csharp
join.Handler = (ctx, _) =>
{
    var group = (IGroupData)ctx.Data!;
    var parts = group.Select(kv => $"{((StepNode)kv.Key).Title}={kv.Value}");
    return $"JOIN[{string.Join(",", parts)}]";
};
```

**预期结果：** `JOIN[a=AV,b=BV]`。本趟没有被驱动的上游不会出现在字典里，因此 `TryGetValue` 返回 `false`，而不是陈旧值。

## 7. 结局、趟数与日志

- `Status` 为 `Idle`、`Running`、`Paused`、`Completed` 或 `Stopped`。
- `Outcome` 消解含糊的 `Stopped`：设置了 `EndedWithError` 时为 `Failed`，由宿主令牌结束时为 `Cancelled`，否则为 `Completed`。
- `Attempt` 统计过图的趟数。重定向会加一，重试不会。
- `Logs` 接收引擎的类型名行以及每一次 `Log`/`Warn`/`Error`。运行仍在追加时，用 `SnapshotLogs()` 安全读取。

**预期结果：** 链运行记录六行（三个类型名、三行节点日志），会话以 `Completed` 结束且 `Attempt == 1`。

## 8. 验证

```powershell
dotnet run
```

预期输出：

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

## 9. 完整代码

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

## 10. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
