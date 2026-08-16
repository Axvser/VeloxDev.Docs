# Workflow Agent — Design Patterns — Memento

The tracker keeps the last snapshot as a `JObject` (originator is the tree, the memento is the JSON). `ComputeDiff` indexes nodes/links by `RuntimeId` and produces `added/removed/modified` collections plus `previous/current` counts.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs`, lines 31-71

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
