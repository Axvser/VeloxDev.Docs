# 工作流自动布局

`Arrange` 为整棵树、或从某个节点可达的子图求一份布局，并把结果作为一次可撤销操作写回。默认求解器先把每个层级对齐到父节点的中心线，再分离重叠的瓦片；宿主选择范围、遍历方向、对既有位置的容忍程度，以及是否真正写入。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 一棵带节点、尺寸和连线的树。不需要适配器或视图：布局作用在模型上。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 默认求解器如何理解一张图

默认规划器运行两个阶段：`HierarchyAlignmentStage` 把每个节点放到其父层级的中线上，`TileSeparationStage` 修补仍然存在的冲突。

- 有多个子节点的父节点会形成**父节点右侧的一列**，按 `RowGap` 堆叠，并在父节点的垂直中心上居中。
- 扇入汇合以其父节点包围盒的中心为中心。
- 单个子节点在父节点上居中。

节点属于包含其中心的那块瓦片；`TileSize` 只改变性能，不改变节点之间应有的关系。

**预期结果：** 对一个位于 `(0,100)` 的 100×40 父节点和三个 100×20 子节点，在 `ColumnGap=64`、`RowGap=10` 下，规范列为 `x=164`，`y=80, 110, 140`。

## 4. 整理一个节点的子图

```csharp
var result = parent.Arrange(new WorkflowLayoutOptions
{
    RowGap = 10,
    ColumnGap = 64,
    TileSize = 64,
    PositionTolerance = 0,
});
```

节点重载通过 `Parent` 找到树，并向其 Helper 索要已注册的 `IWorkflowLayoutSolver`。若 Helper 未实现 `IWorkflowLayoutHost`，则使用默认求解器。`tree.Arrange(options)` 对整棵树做同样的事。

**预期结果：** `result.Applied == true`、`result.AppliedCount == 3`，三个子节点移动到规范列。

## 5. 范围、遍历与固定

给定 `StartNode`（节点重载会自动设置）后，只有可达节点会移动。其余所有几何有限的节点都作为固定障碍留在问题中。

- `Traversal` 选择 `Downstream`、`Upstream` 或 `Both`。
- `MaxDepth` 限制从起始节点出发的跳数；`0` 表示不限。
- `PinStartNode` 默认为 `true`，因此布局从用户选中的节点向外生长。
- `Pinned` 是构建快照时对每个节点求值一次的谓词；被固定的节点永远不会被写入，但仍约束邻居。
- 世界几何非有限的节点会被跳过，并报告为诊断。

**预期结果：** 从父节点向下游整理时，父节点锚点不变，子节点被摆放。

## 6. 容差：严格、默认与宽松

`PositionTolerance` 是每个轴上「接受既有位置、不对齐到规范目标」的距离。

- `0`——严格规范布局；结果不取决于用户把节点留在哪里。
- `8`——默认值；已经位于规范位置 8 个单位以内的组保持原位。
- `32`——宽松；只修补真正的冲突。

无论容差如何，硬重叠与最小间距总会被修复。

**预期结果：** 容差为 `0` 时，两棵起始位置截然不同的树求出相同的坐标。

## 7. 试运行、代价与撤销

`DryRun` 在写入前停住：流水线照常求解，返回一个 `Applied == false`、`DryRun == true` 的正常结果。

```csharp
var dry = parent.Arrange(new WorkflowLayoutOptions { DryRun = true });
```

`result.Solution.Cost` 报告 `Overlaps`、`Crossings`、`Displacement`、`CostMeasured` 与 `CrossingsApproximate`。`MeasureCost = false` 会跳过随图规模增长的 overlap 与 crossing 统计；位移与内容边界始终报告。

应用时通过 `StandardSetAnchor` 写入每个变化节点的**世界**锚点，保留其图层，并把所有写入包进一个 `IActionPair`：

```csharp
tree.GetHelper().Undo();   // 一步恢复所有锚点
```

若节点的实时锚点、图层或父节点在求解与应用之间发生变化，它会被跳过（`result.SkippedCount`），并发编辑永远不会被覆盖。

**预期结果：** 试运行不写任何东西；真实整理后一次撤销恢复原始锚点。

## 8. 替换求解器

把自定义方案注册到某棵树的 Helper 上；它不会影响另一棵树。

```csharp
if (tree.GetHelper() is IWorkflowLayoutHost host)
    host.LayoutSolver = new DefaultWorkflowLayoutSolver(
        planner: new DefaultWorkflowLayoutPlanner(new TolerancePositionPolicy()),
        cost: new DefaultWorkflowLayoutCost());
```

实现 `IWorkflowLayoutSolver` 可替换整个组合，或给默认实现换一个 `IWorkflowLayoutPlanner` / `IWorkflowLayoutCost`。

## 9. 验证

```powershell
dotnet run
```

预期输出：

```text
[layout] applied=True count=3 dryRun=False skipped=0
[layout] c1 -> Anchor(164,80,0)
[layout] c2 -> Anchor(164,110,0)
[layout] c3 -> Anchor(164,140,0)
[layout] overlaps=0 crossings=0 displacement=1873.09 measured=True
[layout] after undo: c1=Anchor(500,-300,0)
[layout] dry applied=False dryRun=True c1=Anchor(500,-300,0)
[layout] scoped parentMoved=False
```

## 10. 完整代码

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.AutoLayout;

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
public partial class DemoNode
{
    public DemoNode(string title) { Title = title; InitializeWorkflow(); }
    [VeloxProperty] private string title = "Node";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

public static class Program
{
    private static void Wire(DemoTree tree, ISlotComponent from, ISlotComponent to)
    {
        tree.GetHelper().SendConnection(from);
        tree.GetHelper().ReceiveConnection(to);
    }

    public static void Main()
    {
        var tree = new DemoTree();
        var parent = new DemoNode("parent") { Anchor = new Anchor(0, 100, 0), Size = new Size(100, 40) };
        var children = new[]
        {
            new DemoNode("c1") { Anchor = new Anchor(500, -300, 0), Size = new Size(100, 20) },
            new DemoNode("c2") { Anchor = new Anchor(1000, 900, 0), Size = new Size(100, 20) },
            new DemoNode("c3") { Anchor = new Anchor(0, 0, 0), Size = new Size(100, 20) },
        };
        foreach (var n in new INodeComponent[] { parent, children[0], children[1], children[2] })
            tree.GetHelper().CreateNode(n);

        parent.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
        foreach (var child in children)
        {
            child.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
            Wire(tree, parent.Output, child.Input);
        }

        var options = new WorkflowLayoutOptions
        {
            RowGap = 10,
            ColumnGap = 64,
            TileSize = 64,
            PositionTolerance = 0,
        };
        var result = parent.Arrange(options);
        Console.WriteLine($"[layout] applied={result.Applied} count={result.AppliedCount} dryRun={result.DryRun} skipped={result.SkippedCount}");
        foreach (var child in children)
            Console.WriteLine($"[layout] {child.Title} -> {child.Anchor}");

        Console.WriteLine($"[layout] overlaps={result.Solution.Cost.Overlaps} crossings={result.Solution.Cost.Crossings} displacement={result.Solution.Cost.Displacement:0.##} measured={result.Solution.Cost.CostMeasured}");

        // One undo restores every anchor the arrangement wrote.
        tree.GetHelper().Undo();
        Console.WriteLine($"[layout] after undo: c1={children[0].Anchor}");

        // A dry run solves but writes nothing.
        var dry = parent.Arrange(new WorkflowLayoutOptions { DryRun = true });
        Console.WriteLine($"[layout] dry applied={dry.Applied} dryRun={dry.DryRun} c1={children[0].Anchor}");

        // Scope: only the reachable downstream subgraph moves; the start node stays put.
        var beforeParent = parent.Anchor;
        parent.Arrange(new WorkflowLayoutOptions { Traversal = WorkflowLayoutTraversal.Downstream, PinStartNode = true });
        Console.WriteLine($"[layout] scoped parentMoved={!Equals(beforeParent, parent.Anchor)}");
    }
}
```

## 11. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
