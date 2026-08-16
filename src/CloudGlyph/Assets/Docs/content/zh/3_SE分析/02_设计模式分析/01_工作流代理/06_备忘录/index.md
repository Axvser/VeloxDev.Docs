# Workflow Agent — 设计模式 — 备忘录

追踪器把最近一次快照存为 `JObject`（发起者是树，备忘录是 JSON）。`ComputeDiff` 按 `RuntimeId` 索引节点/连接，产出 `added/removed/modified` 集合与 `previous/current` 计数。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs`，第 31-71 行

```csharp
public string GetChangesSinceLastSnapshot()
{
    var current = BuildSnapshot();
    if (_lastSnapshot == null)
    {
        _lastSnapshot = current;
        Interlocked.Increment(ref _version);
        return JsonConvert.SerializeObject(new
        {
            status = "full",
            message = "No previous snapshot; returning full state.",
            version = _version,
            state = current
        }, Formatting.Indented);
    }
    var diff = ComputeDiff(_lastSnapshot, current);
    _lastSnapshot = current;
    Interlocked.Increment(ref _version);
    return JsonConvert.SerializeObject(new { status = "diff", version = _version, changes = diff }, Formatting.Indented);
}
```
