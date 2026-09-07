# Workflow Agent — Design Patterns — Command

Every mutation tool dispatches **exactly one** component command (never a direct collection/property write) and awaits its real completion before returning. Because the dispatched command is the same one the GUI fires, the framework's undo/redo stack remains the single source of truth — the toolkit never fabricates its own undo entries.

`MoveNode` is the canonical example: it computes the target `Anchor`, subscribes to the command's `Exited`/`Failed` (`WaitForExitedAsync`), executes `SetAnchorCommand`, and waits. Core records only commands that `Submit` an undoable action, so a move is intentionally non-undoable — exactly matching a manual node drag (verified by `WorkflowLifecycleFidelityTests.MoveNode_ReplaysGuiDragSemantics_AndIsNonUndoable`).

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, lines 415-428

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

Command completion is awaited so the next tool call never observes a stale state window. The wait helpers are:

- `WaitForCommandAsync` — throws on `Failed`, used by the node-execution tools (`ReceiveCommand`, `BroadcastCommand`, `ReverseBroadcastCommand`);
- `WaitForExitedAsync` — completes on the *next* dispatch's exit, used for single-fire commands like `SetAnchorCommand` / `DeleteCommand`;
- `WaitForNDispatchesAsync` — counts `N` exits for shared tree commands dispatched several times per tool call;
- `SendReceiveAsync` — awaits both `Tree.SendConnectionCommand` and `Tree.ReceiveConnectionCommand` (`WorkflowAgentToolkit.cs`, lines 2672-2767).

The compile/run tools extend the same idea: `RunCompiledWorkflow` / `GetNodeResult` dispatch the whole compiled graph through `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` instead of hand-rolling per-node execution — see the [patterns overview](../01_patterns-overview/index.md) and the [data-flow terminal-result page](../../../03_data-flow/01_workflow-agent/04_terminal-result-execution/index.md).
