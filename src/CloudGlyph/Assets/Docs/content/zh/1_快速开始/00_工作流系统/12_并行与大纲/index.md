# 工作流系统 — 并行扇出、并发上限与编译大纲

当一个节点喂给多个下游目标时，编译器把分支包进 `ParallelSegment`，引擎**并发**运行它们。`MaxParallelBranches` 限制同时在飞的分支数。`CompiledOutline` 把任意编译图压平成一份可绑定列表。

## 1. 给图加一个扇出

输出槽接受多条连接的普通节点即可扇出。创建 `FanOutNodes.cs`：

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

**预期结果：** 工程可编译。

## 2. 构建并编译扇出

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

**预期结果：** `ChainSegment, ParallelSegment` —— 源节点编译成单节点链，它的两个目标组成扇出组。`MultipleTargets` 通道让源输出槽接受两条连接；每个输入的 `OneSource` 足以容纳一条入边。

## 3. 分支默认并发

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

**预期结果：** `overlap=True` —— 两个分支同时在对飞。每个分支都从**扇出源节点的负载**开始，绝不会读到兄弟分支的输出。

**说明：** 这是在调用方 `SynchronizationContext` 上交错的异步工作，不是线程并行：每个分支在调用方上下文启动，内部每个 `await` 都让给兄弟分支，所以 I/O 型分支会重叠，而烧 CPU 的分支仍轮流占用线程。这是刻意的 —— 把节点体挪到线程池会破坏「组件是 UI 绑定」的契约。

## 4. 给组加上限

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

**预期结果：** `overlap=False` —— 上限为 1 时，一个分支跑完另一个才开始。

**说明：** 上限是**每组**的，不是每次运行的，并且从具体的 `RuntimeContext` 读取（`ExecutionGateTests` 与 `ParallelExecutionTests` 都钉住这一点）。`null`（默认）表示无上限。当分支很重 —— 每个都启动进程或持有大缓冲区 —— 可设置它，让机器一波波处理。**没有 demo 设置它**；契约由 `ParallelExecutionTests.MaxParallelBranches_SerialisesTheGroupWhenSetToOne` 钉住。

另外两条扇出规则：**任一分支内命中终端分支会结束整个运行**；多个分支请求重定向时，**分支顺序最靠前者胜出**，其余记录日志并忽略（按顺序而非墙钟，保证运行可复现）。

## 5. 把图压平成大纲

```csharp
foreach (var row in CompiledOutline.Of(rootGraph))          // rootGraph: the linear chain
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind} | {row.Label}");
```

**预期结果：**

```text
Execute | TickerNode → BiasNode → PrinterNode
```

每行携带 `Depth`（按它缩进）、`Kind`（`Execute` / `Branch` / `Parallel`，分支选项另有 `Option` / `Terminal`）、`Label` 与它命名的 `Nodes`。对上面的扇出图，你会得到一个深度 0 的 `Parallel` 行，每个分支下各有一行 `Execute`。

**说明：** 编译图本身已经是 view model，嵌套列表可以直接绑定；`CompiledOutline` 服务于另一种形状 —— 一份扁平、可虚拟化的列表，一次显示整个结构。

## 6. 真实仓库中的位置

`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 为它的树视图构建大纲，Avalonia 宿主按 `Depth` 缩进（`Examples/Workflow/Avalonia/Demo/Views/Workflow/DepthIndentConverter.cs`）。demo 的 `WorkflowDemoSession` 编译了带多个扇出的图（`[Stats, Dist, Anomaly]` 组喂给一个 join）。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ParallelExecutionTests.cs` 与 `CompiledOutlineTests.cs`。

前往「验证与运行声明」。
