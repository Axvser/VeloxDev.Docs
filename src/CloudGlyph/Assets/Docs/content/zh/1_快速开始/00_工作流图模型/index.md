# 工作流图模型

一个工作流就是一棵树：树拥有节点，节点拥有插槽，连线把发送端插槽接到接收端插槽。`VeloxDev.Core` 提供四种角色的默认视图模型，以及一个源生成器——它写出 `InitializeWorkflow`、Helper、集合和命令这些管道，节点类只需要声明自己的端口和行为。

## 1. 前置条件

- `VeloxDev.Core` 的目标框架为 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`，任选其一；本示例使用 `net8.0`。
- .NET SDK 9 或更高：生成的组件成员使用 C# 分部属性（`[VeloxProperty] public partial SlotViewModel Input { get; set; }`）。
- 能访问 NuGet 上的 `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**。
- 不需要服务、数据库或密钥——图完全在内存中。

## 2. 安装包

```powershell
dotnet new console -n WorkflowQuickStart
cd WorkflowQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 两个包都出现在项目文件中，`dotnet build` 退出码为 0。生成器包也显式安装：NuGet 引用 `VeloxDev.Core` 已会带上分析器，显式安装生成器包是为了它的构建期 Roslyn 检查；`ProjectReference` 不会传递分析器。

## 3. 声明四种组件角色

每个角色都是一个分部类，标上对应的 `[WorkflowBuilder.*]` 特性。特性的类型参数指定承载其行为的 Helper。

```csharp
[WorkflowBuilder.Tree<DemoTreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

public sealed class DemoTreeHelper : TreeHelper<DemoTree>
{
    public override ILinkComponent CreateLink(ISlotComponent sender, ISlotComponent receiver)
        => new LinkViewModel { Sender = sender, Receiver = receiver };
}
```

树的 Helper 是可选的——替换默认 `TreeHelper` 的意义在于让树创建你自己的连线类型，而不是 `LinkDefaultViewModel`。

```csharp
[WorkflowBuilder.Node<NodeHelper>]
[DefaultSize(220, 120)]
public partial class DemoNode
{
    public DemoNode(string title) { Title = title; InitializeWorkflow(); }

    [VeloxProperty] private string title = "Node";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}
```

这里有两个约定：

- 类型为 `ISlotComponent` 的 `[VeloxProperty]` 成员就是一个**端口**。`InitializeWorkflowCore` 会创建插槽、设置它的 `Parent` 并加入 `Slots`。默认插槽通道是 `MultipleBoth`。
- `[DefaultSize]` 与 `[DefaultAnchor]` 为节点的布局字段提供初值，因此在任何人摆放它之前，节点就已经有几何信息。

**预期结果：** 项目可以编译；每个类已经拥有 `Input`/`Output`、`Slots`、`Parent`、`Anchor`、`Size`、`RuntimeId` 以及各命令属性，而这些代码你一行都没写。

## 4. 搭建一张图

创建树、摆放两个节点、把节点挂上树，再把端口接到端口。

```csharp
var tree = new DemoTree();
tree.Layout.OriginSize = new Size(1600, 900);

var a = new DemoNode("A") { Anchor = new Anchor(60, 80, 0) };
var b = new DemoNode("B") { Anchor = new Anchor(420, 80, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

tree.GetHelper().SendConnection(a.Output);
tree.GetHelper().ReceiveConnection(b.Input);
```

`CreateNode` 是一个可撤销的步骤，而不是裸的 `Nodes.Add`：Helper 先把节点从原树摘下，再提交一个动作对。`SendConnection` 从发送端开始一次拖拽，`ReceiveConnection` 在接收端完成它；两者一起创建连线，并更新 `Links`、`LinksMap`、`Targets` 和 `Sources`。

**预期结果：** `tree.Nodes.Count == 2`、`tree.Links.Count == 1`，且 `tree.Links[0]` 是 `LinkViewModel`。`a.Output.Targets` 包含 `b.Input`，`b.Input.Sources` 包含 `a.Output`。

拓扑查询由标准扩展回答，不需要自己遍历集合：

```csharp
var entries = tree.FindEntryNodeIndices();   // 入度为 0
var exits = tree.FindExitNodeIndices();      // 出度为 0
Console.WriteLine($"entries={string.Join(",", entries)} exits={string.Join(",", exits)}");
Console.WriteLine($"in={tree.GetNodeInDegree(1)} out={tree.GetNodeOutDegree(0)}");
```

**预期结果：** `entries=0`、`exits=1`、`in=1`、`out=1`。

## 5. 几何：视图值与世界值

`Anchor` 和 `Size` 以**世界**坐标存储，但它们的 getter 返回按 `Layout.Scale` 朝画布原点坍缩后的**视图**值。setter 始终接受世界值。

```csharp
Console.WriteLine($"a world={a.GetWorldAnchor()} size={a.Size} layer={a.Anchor.Layer}");

tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine($"zoomed view={a.Anchor} world={a.GetWorldAnchor()}");
```

**预期结果：** 缩放前为 `Anchor(60,80,0)`、`Size(220,120)`；缩放为 `0.5` 后，视图锚点变为 `Anchor(120,160,0)`，而 `GetWorldAnchor()` 仍返回 `Anchor(60,80,0)`。`WorkflowNodeEx.GetWorldAnchor()` 是读取「准备写回的值」的受支持方式。

不要原地修改 `Anchor` 或 `Size` 返回的对象：那是坍缩后的副本。通过属性赋一个新的 `Anchor`/`Size`，或调用 `SetAnchorCommand`/`SetSizeCommand`。

## 6. 验证

运行示例：

```powershell
dotnet run
```

预期输出：

```text
nodes=2 links=1
link type=LinkViewModel
a.Targets=1 b.Sources=1
entries=0 exits=1
a world=Anchor(60,80,0) size=Size(220,120) layer=0
zoomed view=Anchor(120,160,0) world=Anchor(60,80,0)
```

## 7. 完整代码

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.GraphModel;

[WorkflowBuilder.Tree<DemoTreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

public sealed class DemoTreeHelper : TreeHelper<DemoTree>
{
    public override ILinkComponent CreateLink(ISlotComponent sender, ISlotComponent receiver)
        => new LinkViewModel { Sender = sender, Receiver = receiver };
}

[WorkflowBuilder.Node<NodeHelper>]
[DefaultSize(220, 120)]
public partial class DemoNode
{
    public DemoNode(string title) { Title = title; InitializeWorkflow(); }

    [VeloxProperty] private string title = "Node";
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}

public static class Program
{
    public static void Main()
    {
        var tree = new DemoTree();
        tree.Layout.OriginSize = new Size(1600, 900);

        var a = new DemoNode("A") { Anchor = new Anchor(60, 80, 0) };
        var b = new DemoNode("B") { Anchor = new Anchor(420, 80, 0) };
        tree.GetHelper().CreateNode(a);
        tree.GetHelper().CreateNode(b);

        tree.GetHelper().SendConnection(a.Output);
        tree.GetHelper().ReceiveConnection(b.Input);

        Console.WriteLine($"nodes={tree.Nodes.Count} links={tree.Links.Count}");
        Console.WriteLine($"link type={tree.Links[0].GetType().Name}");
        Console.WriteLine($"a.Targets={a.Output.Targets.Count} b.Sources={b.Input.Sources.Count}");
        Console.WriteLine($"entries={string.Join(",", tree.FindEntryNodeIndices())} exits={string.Join(",", tree.FindExitNodeIndices())}");
        Console.WriteLine($"a world={a.GetWorldAnchor()} size={a.Size} layer={a.Anchor.Layer}");

        tree.Layout.Scale = new Scale(0.5, 0.5);
        Console.WriteLine($"zoomed view={a.Anchor} world={a.GetWorldAnchor()}");
    }
}
```

## 8. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
