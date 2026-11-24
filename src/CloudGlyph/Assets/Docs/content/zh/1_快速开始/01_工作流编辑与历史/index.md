# 工作流编辑与历史

每一次结构编辑都表达为组件上的一个命令，而这类命令会把一个 `IActionPair` 记进树的撤销栈。宿主因此不必知道改了什么就能提供撤销/重做，Agent 也正因如此能在同一张图上编辑，而不需要私有 API。

本页接着[工作流图模型](../00_工作流图模型/index.md)；四种组件角色在那里声明。

## 1. 前置条件

- 与图模型页相同的目标框架、SDK 和包：`VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 不需要额外服务或包。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** `dotnet build` 退出码为 0，组件类连同生成的成员一起编译通过。

## 3. 命令集合

每个组件接口都暴露作用于自身的命令。参数一律是普通模型值，所以同一套命令既能服务指针手势和菜单项，也能服务 Agent 工具调用。

| 组件 | 命令 | 参数 |
| --- | --- | --- |
| 树 | `CreateNodeCommand` | `INodeComponent` |
| 树 | `SendConnectionCommand` | `ISlotComponent`（发送端） |
| 树 | `ReceiveConnectionCommand` | `ISlotComponent`（接收端） |
| 树 | `SubmitCommand` | `IActionPair` |
| 树 | `UndoCommand` / `RedoCommand` | 无 |
| 节点 | `SetAnchorCommand` / `SetSizeCommand` / `MoveCommand` | `Anchor` / `Size` / `Offset` |
| 节点 | `CreateSlotCommand` / `DeleteCommand` | `ISlotComponent` / 无 |
| 插槽 | `SetChannelCommand` / `DeleteCommand` | `SlotChannel` / 无 |
| 连线 | `DeleteCommand` | 无 |

```csharp
tree.CreateNodeCommand.Execute(a);
tree.CreateNodeCommand.Execute(b);
tree.SendConnectionCommand.Execute(a.Output);
tree.ReceiveConnectionCommand.Execute(b.Input);
```

**预期结果：** 存在两个节点和一条连线。`CreateNode` 以及那次连线各记一条撤销项。

## 4. 撤销与重做

历史按树保存，由 `WorkflowTreeEx` 承载，可通过 `tree.GetHelper().Undo()/Redo()/ClearHistory()` 或对应命令访问。

```csharp
tree.UndoCommand.Execute(null);      // 移除连线，而不是节点
Console.WriteLine($"links={tree.Links.Count} sources={b.Input.Sources.Count}");

tree.RedoCommand.Execute(null);      // 放回同一条连线
```

**预期结果：** 撤销后 `links=0`、`b.Input.Sources.Count == 0`；重做后 `links=1`。

删除一个带连线的节点是一条原子撤销项：一次撤销会恢复节点、它的插槽、连线以及 `LinksMap`。

```csharp
tree.GetHelper().ClearHistory();
b.DeleteCommand.Execute(null);
Console.WriteLine($"nodes={tree.Nodes.Count} links={tree.Links.Count}");

tree.UndoCommand.Execute(null);
Console.WriteLine($"nodes={tree.Nodes.Count} links={tree.Links.Count}");
```

**预期结果：** 删除后 `nodes=1 links=0`；一次撤销后 `nodes=2 links=1`。撤销历史不是每一次内部集合变更的流水账——它按逻辑操作计数，一次操作一条。

## 5. 提交自己的原子步骤

`SubmitCommand`（或 `tree.GetHelper().Submit(pair)`）会立即执行重做动作并保留撤销动作。当一次用户操作改变了多个值时使用它。

```csharp
var beforeA = a.GetWorldAnchor();
var beforeB = b.GetWorldAnchor();
var toA = new Anchor(beforeA.Horizontal + 40, beforeA.Vertical, beforeA.Layer);
var toB = new Anchor(beforeB.Horizontal + 40, beforeB.Vertical, beforeB.Layer);

tree.SubmitCommand.Execute(new ActionPair(
    () => { a.Anchor = toA; b.Anchor = toB; },
    () => { a.Anchor = beforeA; b.Anchor = beforeB; }));
```

**预期结果：** 两个节点都右移 40 个单位。一次 `UndoCommand` 同时恢复两个原始锚点；一次重做再次同时应用。

有一个标准操作刻意**不**提交动作对：`SetChannelCommand`。通道决定插槽能承载多少连线，因此修改它可能拆掉已有连线——这种拆除不是可撤销编辑。请在搭建阶段、连线之前设置通道。

## 6. 验证

```powershell
dotnet run
```

预期输出：

```text
after connect: nodes=2 links=1
undo connect: links=0 sources=0
redo connect: links=1
after delete: nodes=1 links=0
undo delete: nodes=2 links=1
after pair: a=Anchor(100,80,0) b=Anchor(460,80,0)
undo pair: a=Anchor(60,80,0) b=Anchor(420,80,0)
redo pair: a=Anchor(100,80,0)
```

## 7. 完整代码

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.EditingHistory;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
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

public static class Program
{
    public static void Main()
    {
        var tree = new DemoTree();
        var a = new DemoNode("A") { Anchor = new Anchor(60, 80, 0) };
        var b = new DemoNode("B") { Anchor = new Anchor(420, 80, 0) };

        tree.CreateNodeCommand.Execute(a);
        tree.CreateNodeCommand.Execute(b);
        tree.SendConnectionCommand.Execute(a.Output);
        tree.ReceiveConnectionCommand.Execute(b.Input);
        Console.WriteLine($"after connect: nodes={tree.Nodes.Count} links={tree.Links.Count}");

        tree.UndoCommand.Execute(null);
        Console.WriteLine($"undo connect: links={tree.Links.Count} sources={b.Input.Sources.Count}");

        tree.RedoCommand.Execute(null);
        Console.WriteLine($"redo connect: links={tree.Links.Count}");

        tree.GetHelper().ClearHistory();
        b.DeleteCommand.Execute(null);
        Console.WriteLine($"after delete: nodes={tree.Nodes.Count} links={tree.Links.Count}");

        tree.UndoCommand.Execute(null);
        Console.WriteLine($"undo delete: nodes={tree.Nodes.Count} links={tree.Links.Count}");

        tree.GetHelper().ClearHistory();
        var beforeA = a.GetWorldAnchor();
        var beforeB = b.GetWorldAnchor();
        var toA = new Anchor(beforeA.Horizontal + 40, beforeA.Vertical, beforeA.Layer);
        var toB = new Anchor(beforeB.Horizontal + 40, beforeB.Vertical, beforeB.Layer);

        tree.SubmitCommand.Execute(new ActionPair(
            () => { a.Anchor = toA; b.Anchor = toB; },
            () => { a.Anchor = beforeA; b.Anchor = beforeB; }));
        Console.WriteLine($"after pair: a={a.GetWorldAnchor()} b={b.GetWorldAnchor()}");

        tree.UndoCommand.Execute(null);
        Console.WriteLine($"undo pair: a={a.GetWorldAnchor()} b={b.GetWorldAnchor()}");

        tree.RedoCommand.Execute(null);
        Console.WriteLine($"redo pair: a={a.GetWorldAnchor()}");
    }
}
```

## 8. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
