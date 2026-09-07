# Workflow Agent — 设计模式 — 命令

每个变更工具都**恰好派发一个**组件命令（绝不直接写集合/属性），并在返回前等待其真实完成。由于派发的命令与 GUI 触发的是同一条命令，框架的撤销/重做栈保持唯一真相源——工具包从不伪造自己的撤销条目。

`MoveNode` 是典型示例：计算目标 `Anchor`，订阅命令的 `Exited`/`Failed`（`WaitForExitedAsync`），执行 `SetAnchorCommand` 并等待。Core 只记录 `Submit` 了可撤销动作的命令，因此移动刻意不可撤销——与手动拖拽节点完全一致（由 `WorkflowLifecycleFidelityTests.MoveNode_ReplaysGuiDragSemantics_AndIsNonUndoable` 验证）。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，第 415-428 行

```csharp
private async Task<string> MoveNode(
    [Description("Node index.")] int nodeIndex,
    [Description("Horizontal offset px.")] double offsetX,
    [Description("Vertical offset px.")] double offsetY,
    CancellationToken cancellationToken = default)
{
    if (!TryGetNode(nodeIndex, out var node, out var error)) return error;
    var n = node!;
    var newAnchor = new Anchor(n.Anchor.Horizontal + offsetX, n.Anchor.Vertical + offsetY, n.Anchor.Layer);
    var completion = WaitForExitedAsync(n.SetAnchorCommand, cancellationToken);
    n.SetAnchorCommand.Execute(newAnchor);
    await completion.ConfigureAwait(false);
    return Ok($"Moved {nodeIndex} by ({offsetX},{offsetY}).");
}
```

等待命令完成，保证下一个工具调用不会观察到过期的状态窗口。等待辅助方法有：

- `WaitForCommandAsync` —— `Failed` 时抛错，节点执行工具使用（`ReceiveCommand`、`BroadcastCommand`、`ReverseBroadcastCommand`）；
- `WaitForExitedAsync` —— 在*下一次*派发的退出时完成，用于 `SetAnchorCommand` / `DeleteCommand` 等单发命令；
- `WaitForNDispatchesAsync` —— 为一次工具调用中多次派发的共享树命令计数 N 次退出；
- `SendReceiveAsync` —— 同时等待 `Tree.SendConnectionCommand` 与 `Tree.ReceiveConnectionCommand`（`WorkflowAgentToolkit.cs`，第 2672-2767 行）。

编译/运行工具扩展了同样的思想：`RunCompiledWorkflow` / `GetNodeResult` 通过 `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` 派发整张编译图，而非手工逐节点执行——参见[模式概览](../01_patterns-overview/index.md)与[数据流 Terminal 结果页](../../../03_数据流分析/01_工作流代理/04_Terminal结果执行/index.md)。
