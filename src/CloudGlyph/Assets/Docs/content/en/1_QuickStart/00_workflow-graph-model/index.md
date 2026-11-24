# Workflow graph model

A workflow is one tree that owns nodes, each node owns slots, and each link joins a sender slot to a receiver slot. `VeloxDev.Core` ships the default view models for all four roles and a source generator that writes the plumbing — `InitializeWorkflow`, the helper, the collections and the commands — so a node class only declares its ports and its behaviour.

## 1. Prerequisites

- `VeloxDev.Core` targets `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`. Use any of them; the sample targets `net8.0`.
- .NET SDK 9 or later: the generated component members use C# partial properties (`[VeloxProperty] public partial SlotViewModel Input { get; set; }`).
- NuGet access to `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**.
- No service, database or key is needed — the graph is in memory.

## 2. Install the packages

```powershell
dotnet new console -n WorkflowQuickStart
cd WorkflowQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** both packages appear in the project file, and `dotnet build` exits 0. The generator package is installed explicitly as well: a NuGet reference to `VeloxDev.Core` already carries the analyzer, and the explicit package adds its build-time Roslyn check. A `ProjectReference` to Core does not carry analyzers.

## 3. Declare the four component roles

Each role is a partial class marked with the matching `[WorkflowBuilder.*]` attribute. The attribute's type argument names the helper that carries the behaviour.

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

The tree helper is optional — replacing the default `TreeHelper` is what makes the tree create your own link type instead of `LinkDefaultViewModel`.

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

Two conventions matter here:

- A `[VeloxProperty]` member typed `ISlotComponent` is a **port**. `InitializeWorkflowCore` creates the slot, sets its `Parent` and adds it to `Slots`. The default slot channel is `MultipleBoth`.
- `[DefaultSize]` and `[DefaultAnchor]` seed the node's layout fields, so the node has geometry before anyone places it.

**Expected result:** the project compiles; each class already exposes `Input`/`Output`, `Slots`, `Parent`, `Anchor`, `Size`, `RuntimeId` and the command properties, none of which you wrote.

## 4. Build a graph

Create a tree, place two nodes, attach them, then join a port to a port.

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

`CreateNode` is an undoable step, not a raw `Nodes.Add`: the helper detaches the node from a previous tree, then submits an action pair. `SendConnection` starts a drag from the sender port and `ReceiveConnection` completes it at the receiver; together they create the link and update `Links`, `LinksMap`, `Targets` and `Sources`.

**Expected result:** `tree.Nodes.Count == 2`, `tree.Links.Count == 1`, and `tree.Links[0]` is a `LinkViewModel`. `a.Output.Targets` contains `b.Input`, and `b.Input.Sources` contains `a.Output`.

Topology questions are answered by the standard extensions, not by walking the collections yourself:

```csharp
var entries = tree.FindEntryNodeIndices();   // in-degree 0
var exits = tree.FindExitNodeIndices();     // out-degree 0
Console.WriteLine($"entries={string.Join(",", entries)} exits={string.Join(",", exits)}");
Console.WriteLine($"in={tree.GetNodeInDegree(1)} out={tree.GetNodeOutDegree(0)}");
```

**Expected result:** `entries=0`, `exits=1`, `in=1`, `out=1`.

## 5. Geometry: view values versus world values

`Anchor` and `Size` are stored in **world** coordinates, but their getters return **view** values collapsed toward the canvas origin by `Layout.Scale`. The setter always takes the world value.

```csharp
Console.WriteLine($"a world={a.GetWorldAnchor()} size={a.Size} layer={a.Anchor.Layer}");

tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine($"zoomed view={a.Anchor} world={a.GetWorldAnchor()}");
```

**Expected result:** before zooming, `Anchor(60,80,0)`, `Size(220,120)`; at scale `0.5` the view anchor becomes `Anchor(120,160,0)` while `GetWorldAnchor()` still returns `Anchor(60,80,0)`. `WorkflowNodeEx.GetWorldAnchor()` is the supported way to read a value you intend to write back.

Never mutate the object returned by `Anchor` or `Size`: it is a collapsed copy. Assign a new `Anchor`/`Size` through the property, or call `SetAnchorCommand`/`SetSizeCommand`.

## 6. Verification

Run the sample:

```powershell
dotnet run
```

Expected output:

```text
nodes=2 links=1
link type=LinkViewModel
a.Targets=1 b.Sources=1
entries=0 exits=1
a world=Anchor(60,80,0) size=Size(220,120) layer=0
zoomed view=Anchor(120,160,0) world=Anchor(60,80,0)
```

## 7. Complete code

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

## 8. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
