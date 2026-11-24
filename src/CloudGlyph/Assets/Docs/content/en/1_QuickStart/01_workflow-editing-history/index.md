# Workflow editing and history

Every structural edit is expressed as a command on a component, and every such command records an `IActionPair` on the tree's undo stack. That is what lets a host expose Undo/Redo without knowing what changed, and it is also how the Agent edits the same graph without a private API.

This page continues from [Workflow graph model](../00_workflow-graph-model/index.md); the four component roles are declared there.

## 1. Prerequisites

- The same targets, SDK and packages as the graph-model page: `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- No extra service or package.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** `dotnet build` exits 0 and the component classes compile with their generated members.

## 3. The command set

Each component interface exposes the commands that act on it. Every parameter is a plain model value, which is why the same commands serve a pointer gesture, a menu item and an Agent tool call.

| Component | Command | Parameter |
| --- | --- | --- |
| Tree | `CreateNodeCommand` | `INodeComponent` |
| Tree | `SendConnectionCommand` | `ISlotComponent` (sender) |
| Tree | `ReceiveConnectionCommand` | `ISlotComponent` (receiver) |
| Tree | `SubmitCommand` | `IActionPair` |
| Tree | `UndoCommand` / `RedoCommand` | none |
| Node | `SetAnchorCommand` / `SetSizeCommand` / `MoveCommand` | `Anchor` / `Size` / `Offset` |
| Node | `CreateSlotCommand` / `DeleteCommand` | `ISlotComponent` / none |
| Slot | `SetChannelCommand` / `DeleteCommand` | `SlotChannel` / none |
| Link | `DeleteCommand` | none |

```csharp
tree.CreateNodeCommand.Execute(a);
tree.CreateNodeCommand.Execute(b);
tree.SendConnectionCommand.Execute(a.Output);
tree.ReceiveConnectionCommand.Execute(b.Input);
```

**Expected result:** two nodes and one link exist. `CreateNode` and the connection pair are each one undo entry.

## 4. Undo and redo

The history is kept per tree by `WorkflowTreeEx`, reached through `tree.GetHelper().Undo()/Redo()/ClearHistory()`, or through the commands.

```csharp
tree.UndoCommand.Execute(null);      // removes the link, not the nodes
Console.WriteLine($"links={tree.Links.Count} sources={b.Input.Sources.Count}");

tree.RedoCommand.Execute(null);      // puts the same link back
```

**Expected result:** after Undo, `links=0` and `b.Input.Sources.Count == 0`; after Redo, `links=1` again.

Deleting a node with connections is a single atomic entry: one Undo restores the node, its slots, its links and `LinksMap`.

```csharp
tree.GetHelper().ClearHistory();
b.DeleteCommand.Execute(null);
Console.WriteLine($"nodes={tree.Nodes.Count} links={tree.Links.Count}");

tree.UndoCommand.Execute(null);
Console.WriteLine($"nodes={tree.Nodes.Count} links={tree.Links.Count}");
```

**Expected result:** after delete, `nodes=1 links=0`; one Undo gives `nodes=2 links=1`. The undo history is not a log of every internal collection change — it is one entry per logical operation.

## 5. Submit your own atomic step

`SubmitCommand` (or `tree.GetHelper().Submit(pair)`) applies a redo action immediately and keeps its undo action. Use it when one user action changes several values.

```csharp
var beforeA = a.GetWorldAnchor();
var beforeB = b.GetWorldAnchor();
var toA = new Anchor(beforeA.Horizontal + 40, beforeA.Vertical, beforeA.Layer);
var toB = new Anchor(beforeB.Horizontal + 40, beforeB.Vertical, beforeB.Layer);

tree.SubmitCommand.Execute(new ActionPair(
    () => { a.Anchor = toA; b.Anchor = toB; },
    () => { a.Anchor = beforeA; b.Anchor = beforeB; }));
```

**Expected result:** both nodes move 40 units to the right. One `UndoCommand` restores both original anchors; one Redo applies both again.

One standard operation deliberately does **not** submit a pair: `SetChannelCommand`. A channel decides how many connections a slot may hold, so changing it can tear existing links down — that teardown is not an undoable edit. Set channels during construction, before wiring.

## 6. Verification

```powershell
dotnet run
```

Expected output:

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

## 7. Complete code

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

## 8. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
