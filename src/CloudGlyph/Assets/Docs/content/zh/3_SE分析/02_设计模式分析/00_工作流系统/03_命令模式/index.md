# Workflow System — 设计模式 — 命令模式

编辑器层把每次用户变更都路由到 `IVeloxCommand` 对象。可撤销的变更被表达为 `WorkflowActionPair(redo, undo)`，由 `StandardSubmit` 提交到树的撤销栈（`redo` 立即执行）；`StandardUndo` 弹出栈顶操作对并运行其 `Undo`，随后压入重做栈；`StandardRedo` 相反。两个栈都是存放在每树 `TreeCache` 中的 `ConcurrentStack<IWorkflowActionPair>`。`StandardCreateNode` 是典型示例：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，第 27-40 行

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

Helper 只是这些标准扩展的薄门面（`TreeHelper<T>.Submit/Undo/Redo` 调用 `StandardSubmit/StandardUndo/StandardRedo`），因此像 `SlotEnumerator.SetSelector` 这样的节点级动作也能从任意位置提交一个组合式可撤销操作对（`SlotEnumerator.cs` 第 379-382 行）。

执行模型的关键边界：**编译运行完全绕过命令层**。`RuntimeEngine.DriveAsync` 直接调用 `node.GetHelper().ReceiveAsync(context, ct)`，从不触发 `ReceiveCommand`/`BroadcastCommand`——引擎自己接管下游派发（测试证据：`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`）。广播命令仍是**无状态（非编译）**运行的入口（见[数据流分析](../../../03_数据流分析/00_工作流系统/index.md)）。

*测试证据：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/EntrySemanticsTests.cs`（第 17-38 行）。*
