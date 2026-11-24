# 动态插槽枚举

`SlotEnumerator<TSlot>` 把一个选择器——枚举、`bool` 或自定义 `ISlotProvider`——变成一组端口：每个选择值一个插槽。切换选择器会把整组端口作为一个可撤销步骤重新生成，并按新分支所代表的旧分支重新接上连线。

本页接着[工作流图模型](../00_工作流图模型/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- `[SlotSelectors]` 特性位于 `VeloxDev.AI`（命名空间 `VeloxDev.AI`，程序集 `VeloxDev.Core`）。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过。

## 3. 在节点上声明枚举器

声明一个类型为 `SlotEnumerator<TSlot>` 的 `[VeloxProperty]` 成员；生成器会在 `InitializeWorkflow` 期间创建并安装它，并把每个产出的插槽加入节点的 `Slots`。

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class SelectorNode
{
    public SelectorNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }

    [VeloxProperty]
    [SlotSelectors(typeof(Grade))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}
```

`[SlotSelectors]` 并不驱动枚举器。它声明 **Agent 工具**（`ListSlotProperties` / `SetEnumSlotCollection`）可对该成员使用的选择器类型；在代码里直接调用 `SetSelector` 时，任何枚举、`bool` 或提供器都可以。

**预期结果：** 构造完成后 `node.OutputSlots` 非空，并且即使尚未选择选择器，也已作为 `IConditionalSlotProviders` 条目登记在节点 Helper 上。

## 4. 选择选择器并读取插槽

```csharp
selector.OutputSlots.SetSelector(typeof(Grade));   // Grade { Low, High, Zero }
Console.WriteLine(selector.OutputSlots.Items.Count);          // 3
selector.OutputSlots.CurrentValue = Grade.High;

if (selector.OutputSlots.TrySelect(Grade.High, out var slot))
    tree.GetHelper().SendConnection(slot!);
```

- `Items` 是 `ObservableCollection<ConditionalSlot<TSlot>>`；每项带 `Name`、`Value` 以及为它创建的 `Slot`。
- `TrySelect(value, out slot)` 是路由查找。
- `CurrentValue` 写入的是有类型的值（会按选择器类型归一化），**读出的却是成员文本**，因此它是绑定/显示值。与选择器成员比较前，先用 `NormalizeSelectorValue` 归一化。

**预期结果：** 三个名为 `Low`、`High`、`Zero` 的插槽；`CurrentValue` 读出 `High`；`TrySelect(Grade.High)` 成功，且每个成员对应不同插槽。

## 5. 用提供器描述端口

当端口不是枚举成员时，实现 `ISlotProvider` 并把实例传给 `SetSelector`。每个 `SlotDefinition` 的 `Value` 是路由键，`Label` 是显示名。

```csharp
public sealed class PortProvider(params string[] names) : ISlotProvider
{
    public IEnumerable<SlotDefinition> GetSlots()
        => names.Select(n => new SlotDefinition(n, n));
}

selector.OutputSlots.SetSelector(new PortProvider("stats", "dist", "anomalies"));
```

**预期结果：** 三个名为 `stats`、`dist`、`anomalies` 的插槽。

提供器是**值**，不是类型。用同类型的另一个实例再次调用 `SetSelector`，会按新实例重建端口，而不会恢复上一个实例的快照。正因如此，Agent 的 `SetEnumSlotCollection` 才能反复重塑节点的端口。

若提供器要经过 Agent 的序列化器，请标注 `[Archivable]` 并让端口模型可序列化——否则归档生成器不会为它编译读取器，工具会报「没有已注册的 JSON 读取器」。

## 6. 重新生成、重接线与撤销

`SetSelector` 先记录当前各分支的接线，再构建新集合，然后把每个新分支接回它所代表的旧分支的邻居：

- 在两个**枚举类型**之间，分支按位置代表旧分支（枚举替换不携带名字语义）；
- 对**同一提供器类型**，分支按名字代表旧分支，因此重排端口列表不会悄悄把连线挪到另一个端口。

整次切换是一条撤销项。每个选择器类型最近一次选中的值独立记忆，切回去时分支和选择都会恢复。

```csharp
tree.GetHelper().ClearHistory();
selector.OutputSlots.SetSelector(typeof(Phase));   // Idle, Running, Done
// 已有连线按位置改接到新类型的第一个分支
tree.GetHelper().Undo();                            // 一步：Grade、它的插槽和连线都回来了
```

**预期结果：** 切换后连线数量不变，且落在新类型的第一个分支；一次撤销后选择器恢复为 `Grade`，原分支与连线也恢复。

## 7. 验证

```powershell
dotnet run
```

预期输出：

```text
slots=3: Low,High,Zero
current=High
select High -> True
linked=1, receiverIsLowInput=True
after switch: slots=3: Idle,Running,Done
after switch: links=1, current=Idle
after undo: type=Grade, slots=3, links=1
provider: stats,dist,anomalies
provider rebuilt: stats,dist,anomalies,trend
```

## 8. 完整代码

```csharp
using VeloxDev.AI;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.SlotEnumeration;

public enum Grade { Low, High, Zero }
public enum Phase { Idle, Running, Done }

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
public partial class SelectorNode
{
    public SelectorNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }

    [VeloxProperty]
    [SlotSelectors(typeof(Grade))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class SinkNode
{
    public SinkNode() => InitializeWorkflow();
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
}

/// <summary>A provider describes its ports at run time; the selector type is the provider instance itself.</summary>
public sealed class PortProvider(params string[] names) : ISlotProvider
{
    public IEnumerable<SlotDefinition> GetSlots() => names.Select(n => new SlotDefinition(n, n));
}

public static class Program
{
    public static void Main()
    {
        var tree = new DemoTree();
        var selector = new SelectorNode();
        var low = new SinkNode();
        var high = new SinkNode();
        foreach (var n in new INodeComponent[] { selector, low, high }) tree.GetHelper().CreateNode(n);

        selector.OutputSlots.SetSelector(typeof(Grade));
        Console.WriteLine($"slots={selector.OutputSlots.Items.Count}: {string.Join(",", selector.OutputSlots.Items.Select(i => i.Name))}");

        selector.OutputSlots.CurrentValue = Grade.High;
        Console.WriteLine($"current={selector.OutputSlots.CurrentValue}");
        Console.WriteLine($"select High -> {selector.OutputSlots.TrySelect(Grade.High, out var highSlot)}");

        highSlot!.SetChannelCommand.Execute(SlotChannel.OneTarget);
        low.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
        tree.GetHelper().SendConnection(highSlot);
        tree.GetHelper().ReceiveConnection(low.Input);
        Console.WriteLine($"linked={tree.Links.Count}, receiverIsLowInput={ReferenceEquals(tree.Links[0].Receiver, low.Input)}");

        // Switching the selector type re-materialises the slots and re-wires the links by position.
        tree.GetHelper().ClearHistory();
        selector.OutputSlots.SetSelector(typeof(Phase));
        Console.WriteLine($"after switch: slots={selector.OutputSlots.Items.Count}: {string.Join(",", selector.OutputSlots.Items.Select(i => i.Name))}");
        Console.WriteLine($"after switch: links={tree.Links.Count}, current={selector.OutputSlots.CurrentValue}");

        tree.GetHelper().Undo();
        Console.WriteLine($"after undo: type={selector.OutputSlots.SelectorType?.Name}, slots={selector.OutputSlots.Items.Count}, links={tree.Links.Count}");

        // A provider rebuilds the ports from its own list; branches pair by name.
        selector.OutputSlots.SetSelector(new PortProvider("stats", "dist", "anomalies"));
        Console.WriteLine($"provider: {string.Join(",", selector.OutputSlots.Items.Select(i => i.Name))}");
        selector.OutputSlots.SetSelector(new PortProvider("stats", "dist", "anomalies", "trend"));
        Console.WriteLine($"provider rebuilt: {string.Join(",", selector.OutputSlots.Items.Select(i => i.Name))}");
    }
}
```

## 9. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
