# Workflow editing and history

Every structural change is a command on a component, and each such command records an `IActionPair` on the tree's undo stack. The standard operations that implement those commands are extension methods in `VeloxDev.WorkflowSystem.StandardEx`.

- [Actions and commands](00_actions-and-commands/index.md) — `IActionPair`, `ActionPair`, `WorkflowCommandEx` and the full command set.
- [Tree operations](01_tree-operations/index.md) — `WorkflowTreeEx`: node creation, undo/redo and topology queries.
- [Node, slot and link operations](02_node-slot-link-operations/index.md) — `WorkflowNodeEx`, `WorkflowSlotEx` and `WorkflowLinkEx`.

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(420, 80, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

tree.GetHelper().Undo();          // removes b as one entry
tree.GetHelper().Redo();          // puts it back
Console.WriteLine($"{tree.Nodes.Count}");
```

Connection-building operations (`StandardSendConnection`, `StandardReceiveConnection`, `StandardCheckConnection`, the preview methods) are documented under [Connection rules and preview](../02_connection-rules-preview/index.md) because their rules are part of that feature. For a task-oriented walkthrough, see [Workflow editing and history](../../1_QuickStart/01_workflow-editing-history/index.md).
