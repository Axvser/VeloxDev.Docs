# Dynamic slot enumeration

A `SlotEnumerator<TSlot>` turns one selector — an enum, `bool`, or a custom `ISlotProvider` — into a set of ports: one slot per selector value. Switching the selector re-materialises the whole set as one undoable step, and re-wires the links each new branch stands for.

This page continues from [Workflow graph model](../00_workflow-graph-model/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- The `[SlotSelectors]` attribute lives in `VeloxDev.AI` (namespace `VeloxDev.AI`, assembly `VeloxDev.Core`).

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds.

## 3. Declare the enumerator on a node

Declare a `[VeloxProperty]` member whose type is `SlotEnumerator<TSlot>`; the generator creates and installs it during `InitializeWorkflow` and adds each produced slot to the node's `Slots`.

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

`[SlotSelectors]` does not drive the enumerator. It declares which selector types the **Agent tools** may use for this member (`ListSlotProperties` / `SetEnumSlotCollection`); direct code calls `SetSelector` with any enum, `bool`, or provider.

**Expected result:** `node.OutputSlots` is non-null after construction and registered on the node's helper as an `IConditionalSlotProviders` entry, even before a selector is chosen.

## 4. Choose a selector and read its slots

```csharp
selector.OutputSlots.SetSelector(typeof(Grade));   // Grade { Low, High, Zero }
Console.WriteLine(selector.OutputSlots.Items.Count);          // 3
selector.OutputSlots.CurrentValue = Grade.High;

if (selector.OutputSlots.TrySelect(Grade.High, out var slot))
    tree.GetHelper().SendConnection(slot!);
```

- `Items` is an `ObservableCollection<ConditionalSlot<TSlot>>`; each entry carries `Name`, `Value` and the `Slot` built for it.
- `TrySelect(value, out slot)` is the routing lookup.
- `CurrentValue` writes a typed value (normalised onto the selector type) and **reads back the member's text**, so it is a binding/display value. Use `NormalizeSelectorValue` before comparing it with the selector's members.

**Expected result:** three slots named `Low`, `High`, `Zero`; `CurrentValue` reads `High`; `TrySelect(Grade.High)` succeeds with a distinct slot per member.

## 5. Describe ports with a provider

When the ports are not enum members, implement `ISlotProvider` and pass an instance to `SetSelector`. Each `SlotDefinition`'s `Value` is the routing key; `Label` is the displayed name.

```csharp
public sealed class PortProvider(params string[] names) : ISlotProvider
{
    public IEnumerable<SlotDefinition> GetSlots()
        => names.Select(n => new SlotDefinition(n, n));
}

selector.OutputSlots.SetSelector(new PortProvider("stats", "dist", "anomalies"));
```

**Expected result:** three slots named `stats`, `dist`, `anomalies`.

A provider is a **value**, not a type. Calling `SetSelector` again with another instance of the same type rebuilds the ports from the new instance; it does not restore the previous instance's snapshot. That is why the Agent's `SetEnumSlotCollection` can reshape a node's ports repeatedly.

If the provider is passed through the Agent's serializer, annotate it with `[Archivable]` and make its port model serializable — otherwise the archive generator compiles no reader for it and the tool reports "no registered JSON reader".

## 6. Re-materialisation, rewiring and undo

`SetSelector` captures the current branches' wiring, builds the new set, and reconnects each new branch to the neighbours the old branch it stands for was connected to:

- between two **enum types**, a branch stands for the branch at the same position (an enum swap says nothing about names);
- for the **same provider type**, a branch stands for the branch with the same name, so reordering a port list does not silently move a connection.

The whole switch is one undo entry. Each selector type's last selected value is remembered independently, so switching back restores both its branches and its selection.

```csharp
tree.GetHelper().ClearHistory();
selector.OutputSlots.SetSelector(typeof(Phase));   // Idle, Running, Done
// the existing link is re-routed onto the new type's first branch
tree.GetHelper().Undo();                            // one step: Grade, its slots and its links are back
```

**Expected result:** after the switch the link count is unchanged and the branch is the new type's first; after one Undo the selector is `Grade` again, with the original branch and link restored.

## 7. Verification

```powershell
dotnet run
```

Expected output:

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

## 8. Complete code

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

## 9. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
