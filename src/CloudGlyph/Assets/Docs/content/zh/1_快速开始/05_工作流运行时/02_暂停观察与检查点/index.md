# 暂停、观察与检查点

一次运行可以在节点之间被按住、作为时间线被观察，并被写下来供之后的运行接续。三者都是可选的，配置在 `RuntimeContext` 上；一项都不配时，运行行为与从前完全一致。

本页接着[执行编译图](../00_执行编译图/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 一张编译图和一个节点 Helper；与前面几页的 `StepHelper` 相同。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 在节点之间暂停

`IExecutionGate` 在**每个节点之前**被等待，绝不在节点内部。`ManualExecutionGate` 是手动实现：`Pause()` 把运行按在下一个节点边界，`Resume()` 可从任意线程放行。

```csharp
var gate = new ManualExecutionGate();
var session = new RuntimeContext { Data = "seed", ExecutionGate = gate };
var run = new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);

gate.Resume();   // 或在节点处理器内部调用 Pause()
```

门关着时 `Status` 为 `Paused`，`IsRunning` 仍为 `true`——暂停的运行不是停止的运行。已经开始的节点会跑完，因此暂停不会把一次编辑劈成两半。暂停期间取消运行令牌会结束它（`Status == "Stopped"`，结局 `Cancelled`），而不是让它一直停着。

**预期结果：** 被按住时 `status=Paused running=True completed=False`；`Resume` 之后运行以 `Completed` 结束。

## 4. 观察时间线

`IExecutionObserver` 每个步骤收到一条 `ExecutionObservation`：`RunStarted`、`NodeStarted`、`NodeSucceeded`、`NodeFailed`、`NodeRetried`、`BranchStarted`、`RunEnded`。

```csharp
Observer = new DelegateExecutionObserver(o => observed.Add(o.Kind)),
```

观察项携带节点（运行级/分支级事件为 `null`）、自由格式的细节、趟数 `Attempt` 和耗时。观察者出错不会改变运行：异常被记录，驱动继续。

**预期结果：** 对一条暂停后恢复的两节点链，种类依次为 `RunStarted, NodeStarted, NodeSucceeded, NodeStarted, NodeSucceeded, RunEnded`。

## 5. 把日志导向文件

`ILogWriter` 收到每一条已格式化的行——引擎的和每个节点的。`TextWriterLogWriter.For(path)` 以追加方式打开文件，并拥有该流。

```csharp
var writer = TextWriterLogWriter.For(path);
var session = new RuntimeContext { Data = "seed", LogWriter = writer };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
writer.Dispose();   // 谁打开的流，谁关闭
```

- 行按实际发生的顺序到达，`Logs` 以同样顺序收到同样的行——两个视图可以逐行对照。
- 写入发生在驱动运行的那个线程上。同步写文件会把该 IO 放在那个线程；若在意，请自行排队并在别处排空。
- 写入器抛异常时通过 `RuntimeContext.LogWriteFailed` 上报；行仍保留在 `Logs` 中，运行继续。
- `MaxRetainedLogs` 限制内存视图，而写入器保留全部。默认不设上限是有意为之。

**预期结果：** 文件与 `Logs` 行数相同，首行也相同（`01. StepNode`）。

## 6. 检查点与恢复

`IExecutionCheckpointStore` 在每个节点成功后写入。引擎交出 `RuntimeContext.Snapshot()`；存储保存最新状态，而非历史。

```csharp
var store = new InMemoryCheckpointStore();
var first = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, first, CancellationToken.None);

var place = await store.LoadAsync(CancellationToken.None);
var second = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, second, CancellationToken.None, place);
```

- `ExecutionCheckpoint.Shape` 是图的节点键指纹。恢复到形状不同的图上会在接触会话之前抛出 `InvalidOperationException`。
- 检查点记录为已完成的节点不会被再次驱动。完整跑完后取的检查点恢复时驱动数为零；中断后取的检查点从断点继续。
- `ExecutionCheckpoint.Rekey(checkpoint, graph)` 把检查点重新归档到结构相同、节点身份全新的图上（序列化往返正是这种情况）；它检查节点数量和节点类型，不检查身份。
- 扇出的两个分支可能同时调用 `SaveAsync`；基于文件的实现必须自行串行化写入。

**预期结果：** `shape=3 outputs=3`；恢复的运行不驱动任何节点，报告 `C`，并以 `Completed` 结束。

## 7. 验证

```powershell
dotnet run
```

预期输出：

```text
[gate] while held: status=Paused running=True completed=False
[gate] after resume: status=Completed data=B
[gate] observed=RunStarted,NodeStarted,NodeSucceeded,NodeStarted,NodeSucceeded,RunEnded
[log] inMemory=4 file=4 sameFirst=True
[checkpoint] saved shape=3 outputs=3 attempt=1
[checkpoint] resumed drives=0 output=C status=Completed
```

## 8. 完整代码

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

## 9. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
