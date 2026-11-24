# Connection rules and preview

A connection is accepted only when the framework's rules, the tree helper's own rule and the host's release-time veto all agree. The same rule set powers the drag-time preview, so a green rubber band and a completed link cannot disagree.

This page continues from [Workflow graph model](../00_workflow-graph-model/index.md).

## 1. Prerequisites

- `VeloxDev.Core` and `VeloxDev.Core.Generator` **12.3.0**, .NET SDK 9+.
- No pointer device is required: the preview API is driven by calls, not by a GUI. An adapter normally calls the same methods from its pointer events.

## 2. Install

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the project builds and the component classes compile.

## 3. Channels decide direction and capacity

`SlotChannel` is a flags enum: one direction may point out (`OneTarget`, `MultipleTargets`), into the slot (`OneSource`, `MultipleSources`), or both (`OneBoth`, `MultipleBoth`). The generated slot starts at `MultipleBoth`.

```csharp
a.Output.SetChannelCommand.Execute(SlotChannel.OneTarget);
b.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
```

**Expected result:** `a.Output` may send to one target; `b.Input` may receive from one source.

Two behaviours follow from the channel:

- A port whose channel cannot send is refused as a sender (`SenderCannotSend`); one that cannot receive is refused as a receiver (`ReceiverCannotReceive`).
- Capacity is not a check. Completing a connection **cleans up existing connections** the channel disallows — a `OneTarget` sender drops its previous outgoing link, a `OneSource` receiver drops its previous incoming link. A passing check means "acceptable, possibly after that cleanup".

Changing the channel itself can tear links down, so it is a construction-time setting and not an undoable edit (see [Workflow editing and history](../01_workflow-editing-history/index.md)).

## 4. Ask whether a pair would connect

`StandardCheckConnection` is a pure query: no events, no state changes, no preview. It names the first rule that refused the pair.

```csharp
var check = tree.StandardCheckConnection(a.Output, b.Input);
Console.WriteLine($"A->B valid={check.IsValid} reason={check.Reason}");

var same = tree.StandardCheckConnection(a.Output, a.Input);
Console.WriteLine($"A->A valid={same.IsValid} reason={same.Reason}");
```

**Expected result:** `A->B valid=True reason=None`; `A->A valid=False reason=SameNode`.

The reasons, in the order they are tested:

| `ConnectionRejectReason` | Meaning |
| --- | --- |
| `SenderCannotSend` | The sender's channel has no outgoing direction. |
| `ReceiverCannotReceive` | The receiver's channel has no incoming direction. |
| `SameNode` | Both ports belong to the same node. |
| `RejectedByRule` | The tree helper's `ValidateConnection` returned `false`. |
| `RejectedByHost` | A `PreviewValidating` subscriber refused this preview only. |

## 5. The host's own rule and the release veto

Override `ValidateConnection` on the tree helper to state a rule for the whole editor:

```csharp
public sealed class GuardedTreeHelper : TreeHelper<DemoTree>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => (receiver.Parent as DemoNode)?.Title != "Blocked";
}
```

**Expected result:** the same pair that passed in Step 4 now reports `RejectedByRule` when it targets the node titled `Blocked`.

`ValidateConnection` is asked again on release. For a per-drag refusal that does not subclass the helper, subscribe to `ITreeEvents.Connecting` and set `PreventDefault`; the link is not created. The preview never consults this event — it is a release-time decision.

```csharp
var events = (ITreeEvents)tree.GetHelper();
events.Connecting += (_, e) => e.Handle.PreventDefault = true;
```

**Expected result:** after a refused release, `tree.Links.Count == 0`.

## 6. Drive the drag preview

`WorkflowInput.For(tree)` is the one input route per tree. The adapter reports a candidate slot on every pointer move; the route owns the drag state.

```csharp
var input = WorkflowInput.For(tree);
input.PreviewChanged += (_, e) =>
    Console.WriteLine($"preview {e.State} reason={e.Check?.Reason}");

tree.GetHelper().SendConnection(a.Output);        // Started: sender fixed
tree.StandardSetPreviewReceiver(b.Input);         // ValidTarget
tree.StandardSetPreviewReceiver(blocked.Input);   // InvalidTarget: RejectedByRule
tree.GetHelper().ResetVirtualLink();              // None
```

`ConnectionPreviewState` moves through `Started` → `ValidTarget` / `InvalidTarget` → `None`. The candidate slot also carries the matching `SlotState.PreviewSender` / `SlotState.PreviewReceiver` bit, and `LinkDefaultViewModel` (the default virtual link) implements `IConnectionPreviewLink`, so a link view can paint itself from `Preview`.

A preview may only **tighten** the framework's rules. Subscribe to `PreviewValidating` and call `Reject` to refuse a candidate the framework accepted; a candidate the framework already refused is never offered to you.

```csharp
input.PreviewValidating += (_, e) => e.Reject("blocked by policy");
tree.GetHelper().SendConnection(a.Output);
tree.StandardSetPreviewReceiver(b.Input);
```

**Expected result:** the state becomes `InvalidTarget` with reason `RejectedByHost`; the release-time rules are unchanged.

The same candidate is not re-validated on every pointer move. After an asynchronous verdict lands, call `tree.StandardRefreshConnectionPreview()` to re-run the check for the candidate already under the pointer.

## 7. Verification

```powershell
dotnet run
```

Expected output:

```text
A->B valid=True reason=None
A->A valid=False reason=SameNode
A->Blocked valid=False reason=RejectedByRule
B.Input as sender: valid=False reason=SenderCannotSend
preview Started (sender=True, receiver=False, reason=)
preview ValidTarget (sender=True, receiver=True, reason=None)
preview InvalidTarget (sender=True, receiver=True, reason=RejectedByRule)
preview None (sender=False, receiver=False, reason=)
preview Started (sender=True, receiver=False, reason=)
preview InvalidTarget (sender=True, receiver=True, reason=RejectedByHost)
after preview veto: InvalidTarget / RejectedByHost
preview None (sender=False, receiver=False, reason=)
after release veto: links=0
```

## 8. Complete code

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.ConnectionRules;

[WorkflowBuilder.Node<NodeHelper>]
public partial class DemoNode
{
    public DemoNode() => InitializeWorkflow();
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
    [VeloxProperty] private string title = "Node";
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Tree<GuardedTreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

/// <summary>The host's own rule: a connection into a node titled "Blocked" is refused.</summary>
public sealed class GuardedTreeHelper : TreeHelper<DemoTree>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => (receiver.Parent as DemoNode)?.Title != "Blocked";
}

public static class Program
{
    public static void Main()
    {
        var tree = new DemoTree();
        var a = new DemoNode { Title = "A" };
        var b = new DemoNode { Title = "B" };
        var blocked = new DemoNode { Title = "Blocked" };
        foreach (var n in new[] { a, b, blocked }) tree.GetHelper().CreateNode(n);

        a.Output.SetChannelCommand.Execute(SlotChannel.OneTarget);
        b.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
        blocked.Input.SetChannelCommand.Execute(SlotChannel.OneSource);

        var check = tree.StandardCheckConnection(a.Output, b.Input);
        Console.WriteLine($"A->B valid={check.IsValid} reason={check.Reason}");
        var same = tree.StandardCheckConnection(a.Output, a.Input);
        Console.WriteLine($"A->A valid={same.IsValid} reason={same.Reason}");
        var rule = tree.StandardCheckConnection(a.Output, blocked.Input);
        Console.WriteLine($"A->Blocked valid={rule.IsValid} reason={rule.Reason}");
        var capacity = tree.StandardCheckConnection(b.Input, a.Output);
        Console.WriteLine($"B.Input as sender: valid={capacity.IsValid} reason={capacity.Reason}");

        var input = WorkflowInput.For(tree);
        input.PreviewChanged += (_, e) =>
            Console.WriteLine($"preview {e.State} (sender={e.Sender is not null}, receiver={e.Receiver is not null}, reason={e.Check?.Reason})");

        tree.GetHelper().SendConnection(a.Output);
        tree.StandardSetPreviewReceiver(b.Input);
        tree.StandardSetPreviewReceiver(blocked.Input);
        tree.GetHelper().ResetVirtualLink();

        // A preview-only refusal: the host refuses this candidate without changing the release rules.
        input.PreviewValidating += (_, e) => e.Reject("blocked by policy");
        tree.GetHelper().SendConnection(a.Output);
        tree.StandardSetPreviewReceiver(b.Input);
        Console.WriteLine($"after preview veto: {input.PreviewState} / {input.PreviewCheck?.Reason}");

        // The release-time veto, raised only when the pointer is released.
        var events = (ITreeEvents)tree.GetHelper();
        events.Connecting += (_, e) => e.Handle.PreventDefault = true;
        tree.GetHelper().SendConnection(a.Output);
        tree.GetHelper().ReceiveConnection(b.Input);
        Console.WriteLine($"after release veto: links={tree.Links.Count}");
    }
}
```

## 9. Run declaration

- ✅ Built and ran on 2026-11-25 with .NET SDK 10.0.401 against `VeloxDev.Core` 12.3.0. The run printed exactly the output shown in Verification.
