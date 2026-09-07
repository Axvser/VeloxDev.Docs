# Workflow System — Design Patterns — Command Pattern

The editor layer routes every user mutation through `IVeloxCommand` objects. Undoable mutations are expressed as a `WorkflowActionPair(redo, undo)` submitted onto the tree's undo stack by `StandardSubmit` (which runs the `redo` immediately); `StandardUndo` pops the top pair and runs its `Undo` action before pushing it onto the redo stack; `StandardRedo` does the inverse. Both stacks are `ConcurrentStack<IWorkflowActionPair>` held in a per-tree `TreeCache`.

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, lines 27-40

```csharp
public static void StandardCreateNode(this IWorkflowTreeViewModel component, IWorkflowNodeViewModel node)
{
    var oldParent = node.Parent;
    var newParent = component;
    // Detach the node from its previous tree first. A detached node (first CreateNode)
    // has nothing to detach — skip, otherwise StandardDelete's attachment guard fires.
    if (node.Parent is not null)
    {
        node.GetHelper().Delete();
    }
    component.StandardSubmit(new WorkflowActionPair(
        () => CreateNodeRedo(component, node, newParent),
        () => CreateNodeUndo(component, node, oldParent)));
}
```

The helpers are thin facades over these standard extensions (`TreeHelper<T>.Submit/Undo/Redo` call `StandardSubmit/StandardUndo/StandardRedo`), so a node-level action such as `SlotEnumerator.SetSelector` can submit one composite undoable pair from anywhere.

A key boundary of the execution model: the **compiled run bypasses the command layer entirely**. `RuntimeEngine.DriveAsync` calls `node.GetHelper().ReceiveAsync(context, ct)` directly and never triggers `ReceiveCommand`/`BroadcastCommand` — the engine owns downstream dispatch (`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`). Broadcast commands remain the entry point for stateless (non-compiled) runs.

*Test evidence: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/EntrySemanticsTests.cs`.*
