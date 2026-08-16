# Workflow System — Design Patterns — Command Pattern

Every mutation goes through a command object. Undoable mutations submit a `WorkflowActionPair(redo, undo)` to the tree's undo stack via `StandardSubmit`; `StandardUndo` pops and runs `Undo`, pushing onto the redo stack. `StandardCreateNode` is a canonical example:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, lines 27-40 and 210-239

```csharp
public static void StandardCreateNode(this IWorkflowTreeViewModel component, IWorkflowNodeViewModel node)
{
    var oldParent = node.Parent;
    var newParent = component;
    if (node.Parent is not null)
    {
        node.GetHelper().Delete();
    }
    component.StandardSubmit(new WorkflowActionPair(
        () => CreateNodeRedo(component, node, newParent),
        () => CreateNodeUndo(component, node, oldParent)));
}
```
