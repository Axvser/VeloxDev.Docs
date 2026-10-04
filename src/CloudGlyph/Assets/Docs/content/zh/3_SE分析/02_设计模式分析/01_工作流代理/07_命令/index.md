# Workflow Agent — 设计模式 — 命令

每个变更工具都**恰好派发一个**组件命令（绝不直接写集合/属性），并在返回前等待其真实完成。由于派发的命令与 GUI 触发的是同一条命令，框架的撤销/重做栈保持唯一真相源——工具包从不伪造自己的撤销条目。

`MoveNode` 是典型示例：它以 `Offset` 增量派发 `n.MoveCommand`（`WaitForCommandAsync`）并等待。`MoveCommand` 是 GUI 拖拽节点所走的路径，因此增量按视图空间解释、再按当前缩放换算——刻意*不*去读 `Anchor` 再把和值当作绝对锚点写回：`Anchor` 的 getter 返回被画布缩放*折叠*后的值，读它再把和写回，会让节点在画布缩小时只移动大约一半的距离。Core 只记录 `Submit` 了可撤销动作的命令，因此移动刻意不可撤销——与手动拖拽节点完全一致（由 `WorkflowLifecycleFidelityTests.MoveNode_ReplaysGuiDragSemantics_AndIsNonUndoable` 验证）。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，`MoveNode` 第 674-690 行

```csharp
private async Task<string> MoveNode(
    [Description("Node index.")] int nodeIndex,
    [Description("Horizontal offset px.")] double offsetX,
    [Description("Vertical offset px.")] double offsetY,
    CancellationToken cancellationToken = default)
{
    if (!TryGetNode(nodeIndex, out var node, out var error)) return error;
    var n = node;
    // MoveCommand, not SetAnchorCommand: `node.Anchor`'s getter returns the value *collapsed* by the
    // canvas Scale, so reading it and writing the sum back as an absolute anchor lands the node at
    // roughly half the intended distance whenever the user is zoomed out.
    await WaitForCommandAsync(n.MoveCommand, new Offset(offsetX, offsetY), cancellationToken);
    RefreshSlotAnchors(n);
    return Ok($"Moved {nodeIndex} by ({offsetX},{offsetY}).");
}
```

等待命令完成，保证下一个工具调用不会观察到过期的状态窗口。等待辅助方法有：

- `WaitForCommandAsync` —— 派发命令并等待其真实完成；命令失败（或因被锁而拒绝）时抛错，供每个派发命令的工具使用（`MoveNode`、`SetNodePosition`、`DeleteNode`、`ExecuteNode`、`BroadcastNode` 等）；
- `SendReceiveAsync` —— 同时等待 `Tree.SendConnectionCommand` 与 `Tree.ReceiveConnectionCommand`（`WorkflowAgentToolkit.cs`，第 3239-3242 行）。

编译/运行工具扩展了同样的思想：`RunCompiledWorkflow` / `GetNodeResult` 通过 `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` 派发整张编译图，而非手工逐节点执行——参见[模式概览](../01_模式总览/index.md)与[数据流 Terminal 结果页](../../../03_数据流分析/01_工作流代理/04_Terminal结果执行/index.md)。
