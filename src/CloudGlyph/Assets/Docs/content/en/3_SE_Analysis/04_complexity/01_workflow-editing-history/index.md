# Workflow editing and history

Every edit is expressed as an `ActionPair` — a redo delegate and an undo delegate — pushed onto one of two `ConcurrentStack`s owned by the tree's helper cache. The history machinery itself is constant-time; the cost of an undo is the cost of the operation it replays, not the cost of finding it.

Notation: $K$ recorded actions, $k$ links in one batched edit, $N$ nodes, $S$ slots per node, $d$ degree.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `StandardSubmit` | $O(1)$ + cost of redo | $O(1)$ per action + captured state | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:352` |
| `StandardUndo` | $O(1)$ + cost of undo | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:367` |
| `StandardRedo` | $O(1)$ + cost of redo | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:334` |
| `StandardClearHistory` | $O(1)$ | releases $O(K)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:385` |
| One batched edit over $k$ links | $O(k)$ push + $O(k)$ replay | $O(k)$ closure | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:544` |
| Undo of a node delete | $O(N)$ | — | `Nodes.Contains` then `Nodes.Add` |
| History memory | — | $O(K)$ | two unbounded stacks |

`ActionPair` is a readonly struct of two delegates, so pushing one allocates only a stack node:

```csharp
if (cache.RedoStack.TryPop(out var pair))
{
    try
    {
        pair.Redo.Invoke();
        cache.UndoStack.Push(pair);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:337-342`

## The bound that matters

Undo and redo are not constant in the sense of "cheap"; they are constant in the sense of "no search". The recorded operation is replayed inline:

$$
T_{\text{undo}} = O(1) + T_{\text{action}}
$$

For a single link that is $O(1) + O(d) + O(L)$; for a node delete it is $O(N)$ because re-adding consults `Nodes.Contains`. The batch wrapper is what keeps a multi-link edit one history entry:

```csharp
component.StandardSubmit(new ActionPair(
    () =>
    {
        foreach (var (_, _, link) in connectionsToRemove)
            WorkflowLinkEx.RemoveLinkFromTree(component, link);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:544-548`

## History is unbounded

No depth cap exists in `StandardSubmit`, `StandardUndo` or `StandardRedo`. The two stacks grow with every submitted action, and each entry keeps its captured arguments alive through the delegates. Memory therefore grows linearly with the number of edits since the last clear, and the captured state — slots, links, and in the slot-enumeration case a whole `SelectorState` snapshot — is live object retention, not just a stack node.

```plot
{
  "title": "History memory grows with recorded actions",
  "grid": true,
  "xAxis": { "domain": [0, 200] },
  "yAxis": { "domain": [0, 200] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(K) stack nodes" },
    { "fn": "2*x", "color": "#f472b6", "title": "O(K) with captured state" }
  ]
}
```

The stack operations themselves are $O(1)$ because `ConcurrentStack` is a lock-free linked list; the cache is held in a `ConditionalWeakTable`, so it dies with the tree and needs no explicit teardown.
