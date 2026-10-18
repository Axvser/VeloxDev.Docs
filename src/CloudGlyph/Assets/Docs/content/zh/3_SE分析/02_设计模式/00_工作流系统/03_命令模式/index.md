# 工作流系统 — 设计模式 — 命令模式

编辑器层把每一次用户变更都路由到 `IVeloxCommand` 对象。可撤销变更表达为 `WorkflowActionPair(redo, undo)`，由 `StandardSubmit` 提交到树的撤销栈（它立即运行 `redo`）；`StandardUndo` 弹出栈顶并运行 `Undo`，再压入重做栈；`StandardRedo` 反向执行。两个栈都是 `ConcurrentStack<IWorkflowActionPair>`，存放在每棵树一个的 `TreeCache` 中。

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，25-41 行

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

Helper 是这些标准扩展的薄门面（`TreeHelper<T>.Submit/Undo/Redo` 调用 `StandardSubmit/StandardUndo/StandardRedo`），所以 `SlotEnumerator.SetSelector` 这样的节点级动作可以从任何位置提交一个复合可撤销对。

执行模型的一条关键边界：**编译运行完全绕过命令层**。`RuntimeEngine.DriveAsync` 直接调用 `node.GetHelper().ReceiveAsync(context, ct)`，绝不触发 `ReceiveCommand`/`BroadcastCommand` —— 下游派发归引擎所有（`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`）。广播命令仍是 stateless（非编译）运行的入口。

*测试证据：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/EntrySemanticsTests.cs`。*
