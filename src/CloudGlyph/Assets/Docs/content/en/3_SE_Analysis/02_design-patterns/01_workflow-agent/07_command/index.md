# Workflow Agent — Design Patterns — Command

Every mutation tool dispatches **exactly one** component command (never a direct collection/property write) and awaits its real completion before returning. Because the dispatched command is the same one the GUI fires, the framework's undo/redo stack remains the single source of truth — the toolkit never fabricates its own undo entries.

`MoveNode` is the canonical example: it dispatches `n.MoveCommand` with an `Offset` delta (`WaitForCommandAsync`) and waits. `MoveCommand` is the path a GUI node-drag takes, so the delta is interpreted in view space and scaled by the live scale — deliberately *not* a read of `Anchor` written back as an absolute: `Anchor`'s getter returns the value collapsed by the canvas scale, so reading it and re-writing the sum would land the node at roughly half the intended distance whenever the canvas is zoomed out. Core records only commands that `Submit` an undoable action, so a move is intentionally non-undoable — exactly matching a manual node drag (verified by `WorkflowLifecycleFidelityTests.MoveNode_ReplaysGuiDragSemantics_AndIsNonUndoable`).

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, `MoveNode` lines 674-690

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

Command completion is awaited so the next tool call never observes a stale state window. The wait helpers are:

- `WaitForCommandAsync` — dispatches a command and awaits its real completion; throws when the command fails (or is refused because it is locked), used by every command-dispatching tool (`MoveNode`, `SetNodePosition`, `DeleteNode`, `ExecuteNode`, `BroadcastNode`, …);
- `SendReceiveAsync` — awaits both `Tree.SendConnectionCommand` and `Tree.ReceiveConnectionCommand` (`WorkflowAgentToolkit.cs`, lines 3239-3242).

The compile/run tools extend the same idea: `RunCompiledWorkflow` / `GetNodeResult` dispatch the whole compiled graph through `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` instead of hand-rolling per-node execution — see the [patterns overview](../01_patterns-overview/index.md) and the [data-flow terminal-result page](../../../03_data-flow/01_workflow-agent/04_terminal-result-execution/index.md).
