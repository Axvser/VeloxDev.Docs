# Workflow Agent — 设计模式 — 命令

每个变更工具恰好派发一个组件命令并等待其完成（`WaitForExitedAsync` 在派发前订阅 `Exited`/`Failed`）。因此框架撤销/重做栈保持唯一真相源 —— 工具包从不伪造自己的撤销条目。

> 源码：`WorkflowAgentToolkit.cs`，第 411-425 与 2656-2675 行

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
