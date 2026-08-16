# Workflow Agent — Design Patterns — Command

Each mutation tool dispatches exactly one component command and awaits its completion (`WaitForExitedAsync` subscribes to `Exited`/`Failed` before dispatching). The framework's undo/redo stack therefore remains the single source of truth — the toolkit never fabricates its own undo entries.

> Source: `WorkflowAgentToolkit.cs`, lines 411-425 and 2656-2675

```csharp
private async Task<string> MoveNode(int nodeIndex, double offsetX, double offsetY, CancellationToken ct)
{
    if (!TryGetNode(nodeIndex, out var node, out var error)) return error;
    var n = node!;
    var newAnchor = new Anchor(n.Anchor.Horizontal + offsetX, n.Anchor.Vertical + offsetY, n.Anchor.Layer);
    var completion = WaitForExitedAsync(n.SetAnchorCommand, ct);
    n.SetAnchorCommand.Execute(newAnchor);
    await completion.ConfigureAwait(false);
    return Ok($"Moved {nodeIndex} by ({offsetX},{offsetY}).");
}
```
