# Connection rules and preview

A connection is accepted only when the framework's rules, the tree helper's `ValidateConnection` and the release-time `Connecting` veto all agree. The drag-time preview runs the same framework rules, so a green rubber band and a completed link cannot disagree about them.

The surface splits into the rule set and the drag state:

- [Connection rules](00_connection-rules/index.md) — `ConnectionCheck`, `ConnectionRejectReason`, `SlotChannel`, `SlotState`, and the standard check/send/receive/reset operations.
- [Connection preview](01_connection-preview/index.md) — `WorkflowInput`, `ConnectionPreviewState`, `IConnectionPreviewLink`, the preview methods, `ITreeEvents` and the event arguments.

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel();
var b = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
a.CreateSlotCommand.Execute(from);
b.CreateSlotCommand.Execute(to);

var check = tree.StandardCheckConnection(from, to);
Console.WriteLine(check);   // Valid
```

For a task-oriented walkthrough, see [Connection rules and preview](../../1_QuickStart/02_connection-rules-preview/index.md).
