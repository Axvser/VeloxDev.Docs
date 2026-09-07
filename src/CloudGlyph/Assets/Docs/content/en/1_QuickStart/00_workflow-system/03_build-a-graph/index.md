# Workflow System — Build the Graph

Add a `Program.cs` (a static `Main` in `WorkflowQuickStart`) and build the three-node chain `Ticker → Bias → Printer`. The steps below are fragments of one `Build()` method — place each inside it, in order, before `return tree;`. All the calls are the tree helper API used by the demo session builder (`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`).

## 1. Create the tree and register the nodes

```csharp
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

public static class GraphBuilder
{
    public static QuickTree Build()
    {
        var tree = new QuickTree();
        tree.Layout.OriginSize = new Size(2400, 850);
        var helper = tree.GetHelper();

        var ticker = new TickerNode { Anchor = new Anchor(60, 60, 0) };
        var bias = new BiasNode { Anchor = new Anchor(460, 60, 0) };
        var printer = new PrinterNode { Anchor = new Anchor(860, 60, 0) };

        helper.CreateNode(ticker);
        helper.CreateNode(bias);
        helper.CreateNode(printer);

        return tree;
    }
}
```

`helper.CreateNode(node)` (a method on `IWorkflowTreeViewModelHelper`) submits an undoable `WorkflowActionPair` and adds the node to `tree.Nodes` — see `StandardCreateNode` in `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`.

**Expected result:** `tree.Nodes.Count == 3`; each node's `Parent` references the tree; the undo stack holds one entry per `CreateNode`.

## 2. Configure the slot channels

A slot's `SlotChannel` (a `[Flags]` enum in `VeloxDev.WorkflowSystem`) declares connection capacity per direction: `OneSource` = at most one incoming connection, `OneTarget` = at most one outgoing connection (`Src/Core/VeloxDev.Core/WorkflowSystem/Enums/Slot.cs`). Set it through the slot's `SetChannelCommand`, never by replacing the generated slot with a new instance (the demo warns that replacing a preset slot triggers its `DeleteCommand` and creates ghost undo entries):

```csharp
private static void SetChannel(QuickSlot slot, SlotChannel channel)
    => slot.SetChannelCommand.Execute(channel);
```

Configure the three active edges: `Ticker.Output`, `Bias.Input`, `Bias.Output`, `Printer.Input`:

```csharp
SetChannel(ticker.OutputSlot, SlotChannel.OneTarget);
SetChannel(bias.InputSlot, SlotChannel.OneSource);
SetChannel(bias.OutputSlot, SlotChannel.OneTarget);
SetChannel(printer.InputSlot, SlotChannel.OneSource);
```

**Expected result:** each configured slot reports its new `Channel`; no undo entries are created (`SetChannelCommand` is a standard, non-undoable path).

## 3. Connect the slots

The connection protocol is two-phase on the tree helper: `SendConnection(outputSlot)` opens a preview from the sender, `ReceiveConnection(inputSlot)` validates capacity and user rules, cleans up conflicting same-direction links, then creates the `QuickLink` — submitted as one undoable action (see `StandardSendConnection` / `StandardReceiveConnection` in `WorkflowTreeEx.cs`):

```csharp
helper.SendConnection(ticker.OutputSlot!);
helper.ReceiveConnection(bias.InputSlot!);

helper.SendConnection(bias.OutputSlot!);
helper.ReceiveConnection(printer.InputSlot!);
```

**Expected result:** `tree.Links.Count == 2`; `tree.LinksMap[ticker.OutputSlot][bias.InputSlot]` and `tree.LinksMap[bias.OutputSlot][printer.InputSlot]` are set; `bias.InputSlot.Sources` contains `ticker.OutputSlot` and `bias.OutputSlot.Targets` contains `printer.InputSlot`. `tree.UndoCommand.Execute(null)` removes both links; `tree.RedoCommand.Execute(null)` restores them.

The topology the compiler consumes is exactly these slot `Targets` / `Sources` edges. Go to [Compile & run forward](../04_compile-and-run/index.md).
