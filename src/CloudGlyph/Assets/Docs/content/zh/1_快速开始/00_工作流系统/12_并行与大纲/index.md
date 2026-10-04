# Workflow System — 并行扇出、它的并发上限与编译大纲

当一个节点喂给多个下游目标时，编译器把这些分支包进一个 `ParallelSegment`，引擎让它们**并发**运行。`MaxParallelBranches` 限制同时有多少条在飞。`CompiledOutline` 把任何编译图压成一条可绑定的列表。

## 1. 给图加一个扇出

输出槽位可以接受多条连线的普通节点就会扇出。创建 `FanOutNodes.cs`：

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

// 两条分支各自记下开始与结束时刻，好在外部量出重叠。
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

**预期结果：** 编译通过。

## 2. 搭出并编译这个扇出

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

**预期结果：** `ChainSegment, ParallelSegment` —— 源编译成一条单节点链，它的两个目标变成一个扇出组。`MultipleTargets` 通道是源的输出槽位能接受两条连线的原因；每个输入端的 `OneSource` 就够接一条入边了。

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

**预期结果：** `overlap=True` —— 两条分支同时在飞。每条分支都从**扇出源的载荷**出发，绝不会读到兄弟的产物。

**说明：** 这是调用方 `SynchronizationContext` 上的交错异步工作，不是线程并行：每条分支都在调用方上下文上起步，它内部每次 `await` 都会让给兄弟，所以 I/O 密集的分支会重叠，而烧 CPU 的分支仍然轮流占用那个线程。这是刻意的 —— 把节点体挪到线程池会破坏「组件与 UI 绑定」这条契约。

## 4. 给这个组加上限

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

**预期结果：** `overlap=False` —— 上限为 1 时，一条分支跑完下一条才开始。

**说明：** 上限是**按组**的，不是按轮的，而且它是从具体的 `RuntimeContext` 上读的（`ExecutionGateTests` 与 `ParallelExecutionTests` 都钉住了这一点）。`null`（默认）表示不限。分支很重时 —— 每一条都起进程、占大缓冲 —— 设上它，让机器分波处理。**没有 demo 设置它**；契约由 `ParallelExecutionTests.MaxParallelBranches_SerialisesTheGroupWhenSetToOne` 钉住。

还有两条扇出规矩值得记住：**任意分支内命中终结分支即整轮结束**；多条分支同时请求重定向时**分支顺序第一条**胜出，其余记日志忽略（按顺序而不是按墙上时钟，运行因此可复现）。

## 5. 把图压成一条大纲

```csharp
foreach (var row in CompiledOutline.Of(rootGraph))          // rootGraph：那条线性链
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind} | {row.Label}");
```

**预期结果：**

```text
Execute | TickerNode → BiasNode → PrinterNode
```

每行带 `Depth`（按它缩进）、`Kind`（`Execute` / `Branch` / `Parallel`，外加分支选项的 `Option` / `Terminal`）、`Label` 与它点名的 `Nodes`。对上面那张扇出图，你会得到深度 0 的一行 `Parallel`，下面每条分支一行 `Execute`。

**说明：** 编译图本身就是 ViewModel，所以嵌套列表可以直接绑它；`CompiledOutline` 是为另一种形态准备的 —— 一个扁平、可虚拟化的列表，一次把整棵结构摆出来。

## 6. 真实仓库里它在哪

`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 为树视图构建这份大纲，Avalonia 宿主按 `Depth` 缩进（`Examples/Workflow/Avalonia/Demo/Views/Workflow/DepthIndentConverter.cs`）。demo 的 `WorkflowDemoSession` 编译出的图里有好几处扇出（`[Stats, Dist, Anomaly]` 那一组就汇入一个汇合点）。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ParallelExecutionTests.cs` 与 `CompiledOutlineTests.cs`。

下一步见 `13_验证与运行声明`。
