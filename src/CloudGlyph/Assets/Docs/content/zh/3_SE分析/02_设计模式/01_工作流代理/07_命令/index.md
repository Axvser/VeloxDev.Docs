# 工作流代理 —— 设计模式 —— 命令

每个变更工具**恰好派发一条**组件命令（绝不直接写集合/属性），并等待其真实完成后再返回。因为派发的命令与 GUI 触发的是同一条，框架的撤销/重做栈仍是唯一事实源 —— 工具包从不伪造自己的撤销条目。

`MoveNode` 是典型例子：它用 `Offset` 增量派发 `n.MoveCommand`（`WaitForCommandAsync`）并等待。`MoveCommand` 正是 GUI 节点拖拽走的路径，因此增量按视图空间解释、按实时缩放换算 —— 刻意*不*读取 `Anchor` 再写回绝对值：`Anchor` 的 getter 返回被画布缩放折叠后的值，读它再把和写回去，会在画布缩小时把节点落到大约一半的预期距离。Core 只记录 `Submit` 了可撤销动作的命令，因此移动刻意不可撤销 —— 与手工节点拖拽完全一致（由 `WorkflowLifecycleFidelityTests.MoveNode_ReplaysGuiDragSemantics_AndIsNonUndoable` 验证）。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，`MoveNode`

```csharp
private async Task<string> MoveNode(
    [Description("Node index.")] int nodeIndex,
    [Description("Horizontal offset px.")] double offsetX,
    [Description("Vertical offset px.")] double offsetY,
    CancellationToken cancellationToken = default)
{
    if (!TryGetNode(nodeIndex, out var node, out var error)) return error;
    var n = node;
    // MoveCommand，而不是 SetAnchorCommand：`node.Anchor` 的 getter 返回被
    // 画布 Scale 折叠后的值，读它再把和写回绝对锚点，会在用户缩小时把节点
    // 落到大约一半的预期距离。
    await WaitForCommandAsync(n.MoveCommand, new Offset(offsetX, offsetY), cancellationToken);
    RefreshSlotAnchors(n);
    return Ok($"Moved {nodeIndex} by ({offsetX},{offsetY}).");
}
```

等待命令完成，使下一次工具调用永远不会看到过期的状态窗口。等待辅助：

- `WaitForCommandAsync` —— 派发命令并等待真实完成；命令失败（或因锁定被拒）时抛出。所有派发命令的工具都用它（`MoveNode`、`SetNodePosition`、`DeleteNode`、`ExecuteNode`、`BroadcastNode` 等）。
- `SendReceiveAsync` —— 同时等待 `Tree.SendConnectionCommand` 与 `Tree.ReceiveConnectionCommand`。

编译/运行工具延续同一思路：`RunCompiledWorkflow` / `GetNodeResult` 通过 `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` 派发整张编译图，而不是手写逐节点执行 —— 见[模式总览](../01_模式总览/index.md)与[数据流 · 终结点结果](../../../03_数据流/01_工作流代理/04_终结点结果执行/index.md)。
