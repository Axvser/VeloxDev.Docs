# Workflow Agent — Design Patterns — Memento

`WorkflowStateTracker` gives the Agent memento-style change observation with minimal context: `TakeSnapshot` stores the current tree state as a JSON `JObject` (the *memento*), and `GetChangesSinceLastSnapshot` compares the stored snapshot against a freshly built one and returns a property-level diff — added/removed/modified nodes and links by `RuntimeId` — instead of making the agent re-read the full state each turn.

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

    return JsonConvert.SerializeObject(new
    {
        status = "diff",
        version = _version,
        changes = diff
    }, Formatting.Indented);
}
```

`ComputeDiff` indexes nodes and links by `RuntimeId` (via each component's `IWorkflowIdentifiable.Helper`) and only compares scalar/enum properties through `JToken.DeepEquals`, so the diff never materializes full subtree comparisons (`WorkflowStateTracker.cs`, lines 73-192). The toolkit owns one tracker per scope (`WorkflowAgentToolkit.cs`, line 27) and exposes it through the `TakeSnapshot` and `GetChangesSinceSnapshot` tools. The underlying workflow commands (Core's undo/redo) are the originator's own history mechanism; this tracker is a lightweight, orthogonal view over the same graph.
