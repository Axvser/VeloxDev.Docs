# Workflow System — 设计模式 — 命令模式

每个变更都经过命令对象。可撤销操作通过 `StandardSubmit` 把 `WorkflowActionPair(redo, undo)` 提交到撤销栈；`StandardUndo` 弹出并执行 `Undo`，压入重做栈。`StandardCreateNode` 是典型示例：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，第 27-40 与 210-239 行

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
