# 分支与终止编译

路由器把图变成 `BranchSegment`：`GetRouteTable` 声明「键 → 下游节点」，`ResolveRouteKey` 决定一次运行走哪个键。同一契约既支持编译期决定（静态），也支持运行期决定（动态）。从终止节点编译则反向走，只保留计算某个节点所需的祖先锥。

本页接着[根节点编译](../00_根节点编译/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 根节点编译页中的图与组件声明。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 声明路由器

路由器就是实现了 `ICompileTimeRouter` 的普通节点。它的分支端口仍来自[动态插槽枚举](../../03_动态插槽枚举/index.md)里的 `SlotEnumerator<TSlot>`。

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter
{
    public RouterNode(string title) { Title = title; InitializeWorkflow(); }

    [VeloxProperty] public partial SlotViewModel Input { get; set; }

    [VeloxProperty]
    [SlotSelectors(typeof(RouteKey))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public RouterCompileMode Mode { get; set; } = RouterCompileMode.Dynamic;
    public object? Selection { get; set; } = RouteKey.A;
    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(Mode == RouterCompileMode.Dynamic && payload is null ? null : Selection);

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Mode == RouterCompileMode.Static && Selection is not null && Routes.TryGetValue(Selection, out var only)
                ? new Dictionary<object, IReadOnlyList<INodeComponent>> { [Selection] = only }
                : Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }
}
```

`RouterCompileMode` 是本示例自己的策略。`ICompileTimeRouter` 只问两个问题，路由器可以从自己持有的任何状态作答。

**预期结果：** 路由器可达时编译为 `BranchSegment`，每个路由键一个 `BranchOption`。

## 4. 路由表与路由键

- `GetRouteTable()` 在编译期调用。节点列表为空的条目是**终止选项**：运行期选中它会结束整次运行。
- `ResolveRouteKey(payload)` 在编译期以 `null` 调用，运行期以会话调用。编译期返回 `null` 表示「现在无法决定」→ 分支是**动态**的，所有选项都留在图里；返回某个键则表示**静态**，该键被锁定为 `CompileKey`。

```csharp
router.OutputSlots.SetSelector(typeof(RouteKey));
router.Routes[RouteKey.A] = [x];
router.Routes[RouteKey.B] = [y];
if (router.OutputSlots.TrySelect(RouteKey.A, out var slotA)) Wire(tree, slotA!, x.Input);
if (router.OutputSlots.TrySelect(RouteKey.B, out var slotB)) Wire(tree, slotB!, y.Input);
```

**预期结果：** 每个分支插槽都接到自己的工作节点，拓扑与路由表一致。

## 5. 静态剪枝与动态分支

```csharp
var dynamicGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
var dynamicBranch = (BranchSegment)dynamicGraph.Entries[1];
// options=2, IsDynamic=True, CompileKey=null

router.Mode = RouterCompileMode.Static;
router.Selection = RouteKey.A;
var staticGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
var staticBranch = (BranchSegment)staticGraph.Entries[1];
// options=1, IsDynamic=False, CompileKey=A
```

静态模式下，未选中的分支不只是运行期跳过：它的下游节点会被访问并获得 `Order = -1`（绝对停止状态），且不出现在任何段里。`graph.TryGetCompileInfo(y, out _)` 仍返回 `true` 且 `Order == -1`；`CompiledOutline` 不会列出它。

**预期结果：** 动态报告两个选项，`x=2, y=3`；静态报告一个选项，`x=2, y=-1`。

## 6. 路由键内部的扇出

若一个路由键映射到多个下游节点，编译器会分别递归编译它们，并包进该选项子图内的 `ParallelSegment`。所有分支出口共同指向的节点成为汇合点，也是父图中下一条链的起点。拥有多个有效下游的普通（非路由器）节点会以同样方式分解。

## 7. 终止编译

`CompileRole.Terminal` 接收「你要其结果的那个节点」，沿 `Sources` 收集其祖先锥，推导该锥自己的入口边界，只编译计算该节点所必需的部分。

```csharp
var cone = (await compiler.CompileAsync(y, CompileRole.Terminal))[0];
```

在锥内，兄弟分支是**不存在**，而不是被停止：`x` 完全没有编译绑定。若路由器有不止一条分支能到达目标，该锥会被拒绝并抛出 `InvalidOperationException`——一次正向运行只能走一条分支，需要两条分支才能得出的结果不会被捏造。

运行期把 `RuntimeContext.Target` 设为终止节点。只有该节点确实被驱动过，`TargetReached` 才为 `true`。对于上面的动态路由器，锥保留了到达 `y` 的分支，但运行仍必须选中那个键。

```csharp
router.Selection = RouteKey.B;
var session = new RuntimeContext { Data = "seed", Target = y };
await new RuntimeEngine().RunAsync(cone, session, CancellationToken.None);
```

**预期结果：** `status=Completed`、`targetReached=True`。

## 8. 验证

```powershell
dotnet run
```

预期输出：

```text
[dynamic] options=2 isDynamic=True key=null
[dynamic] x=2 y=3
[static] options=1 isDynamic=False key=A
[static] x=2 y=-1
[terminal] entries=ChainSegment,BranchSegment
[terminal] x=- y=2; containsSource=True
[terminal] status=Completed targetReached=True depth=4
```

## 9. 完整代码

```csharp
using VeloxDev.AI;
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace QuickStart.Compiler.Branches;

public enum RouteKey { A, B }

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

[WorkflowBuilder.Node<NodeHelper>]
public partial class StepNode
{
    public StepNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Step";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter
{
    public RouterNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Router";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty]
    [SlotSelectors(typeof(RouteKey))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public RouterCompileMode Mode { get; set; } = RouterCompileMode.Dynamic;
    public object? Selection { get; set; } = RouteKey.A;
    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(Mode == RouterCompileMode.Dynamic && payload is null ? null : Selection);

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Mode == RouterCompileMode.Static && Selection is not null && Routes.TryGetValue(Selection, out var only)
                ? new Dictionary<object, IReadOnlyList<INodeComponent>> { [Selection] = only }
                : Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }
}

public static class Program
{
    private static void Wire(DemoTree tree, ISlotComponent from, ISlotComponent to)
    {
        tree.GetHelper().SendConnection(from);
        tree.GetHelper().ReceiveConnection(to);
    }

    private static string OrderOf(CompiledGraph graph, INodeComponent node)
        => graph.TryGetCompileInfo(node, out var info) ? info!.Order.ToString() : "-";

    public static async Task Main()
    {
        var tree = new DemoTree();
        var source = new StepNode("source");
        var router = new RouterNode("router");
        var x = new StepNode("x");
        var y = new StepNode("y");
        foreach (var n in new INodeComponent[] { source, router, x, y }) tree.GetHelper().CreateNode(n);
        Wire(tree, source.Output, router.Input);

        router.OutputSlots.SetSelector(typeof(RouteKey));
        router.Routes[RouteKey.A] = [x];
        router.Routes[RouteKey.B] = [y];
        if (router.OutputSlots.TrySelect(RouteKey.A, out var slotA)) Wire(tree, slotA!, x.Input);
        if (router.OutputSlots.TrySelect(RouteKey.B, out var slotB)) Wire(tree, slotB!, y.Input);

        var compiler = new CompilerViewModel();

        var dynamicGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
        var dynamicBranch = (BranchSegment)dynamicGraph.Entries[1];
        Console.WriteLine($"[dynamic] options={dynamicBranch.Options.Count} isDynamic={dynamicBranch.IsDynamic} key={dynamicBranch.CompileKey ?? "null"}");
        Console.WriteLine($"[dynamic] x={OrderOf(dynamicGraph, x)} y={OrderOf(dynamicGraph, y)}");

        router.Mode = RouterCompileMode.Static;
        router.Selection = RouteKey.A;
        var staticGraph = (await compiler.CompileAsync(source, CompileRole.Root))[0];
        var staticBranch = (BranchSegment)staticGraph.Entries[1];
        Console.WriteLine($"[static] options={staticBranch.Options.Count} isDynamic={staticBranch.IsDynamic} key={staticBranch.CompileKey}");
        Console.WriteLine($"[static] x={OrderOf(staticGraph, x)} y={OrderOf(staticGraph, y)}");

        router.Mode = RouterCompileMode.Dynamic;
        var cone = (await compiler.CompileAsync(y, CompileRole.Terminal))[0];
        Console.WriteLine($"[terminal] entries={string.Join(",", cone.Entries.Select(e => e.GetType().Name))}");
        Console.WriteLine($"[terminal] x={OrderOf(cone, x)} y={OrderOf(cone, y)}; containsSource={cone.TryGetCompileInfo(source, out _)}");

        router.Selection = RouteKey.B;   // the cone kept only the branch that reaches y
        var session = new RuntimeContext { Data = "seed", Target = y };
        await new RuntimeEngine().RunAsync(cone, session, CancellationToken.None);
        Console.WriteLine($"[terminal] status={session.Status} targetReached={session.TargetReached} depth={CompiledOutline.Of(cone).Count}");
    }
}
```

## 10. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
