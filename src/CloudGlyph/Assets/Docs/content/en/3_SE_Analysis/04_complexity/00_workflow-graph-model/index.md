# Workflow graph model

The graph model is four cooperating collections: `Nodes` and `Links` on the tree, `Slots` on each node, and a two-level `LinksMap` keyed by the sender and receiver slot. Almost every cost below follows from one fact: the collections are `ObservableCollection<T>` (a `List<T>` underneath), so indexed access and `Add` are constant-time, while `Contains` and `Remove` are linear scans. The `LinksMap` is the one hash index in the model.

Notation: $N$ nodes, $S$ slots per node, $d$ links incident to one slot, $L$ links in the tree, $V$ and $E$ the nodes and slot edges of a reachable subgraph.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `StandardCreateNode`, detached | $O(1)$ amortized | $O(1)$ + $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:28` |
| `StandardCreateNode`, re-parenting | $O(S d + N)$ | — | the first call deletes from the old tree |
| `StandardCreateSlot` | $O(S)$ per call, $O(S^2)$ to build a node | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:24` |
| Delete a node | $O(S d + N)$ | $O(S d)$ temporary | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:295` |
| Add / remove a link | $O(1) + O(d) + O(L)$ | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:17` |
| In/out degree of one node | $O(S)$ | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:592` |
| Find entry / exit nodes | $O(N S)$ | $O(N)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:625` |
| Forward / reverse BFS | $O(V + E)$ | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:227` |
| Lookup a link by its endpoints | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:42` |
| Lookup a node by index | $O(1)$ | — | list-backed `Nodes` indexer |
| Lookup a node by `RuntimeId` | $O(N)$ — *inferred* | — | no Core index exists |
| Spatial query (virtualized trees) | $O(C + H)$ | $O(C)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:98` |

The `LinksMap` probe is what makes link work constant-time where it can be:

```csharp
if (tree.LinksMap.TryGetValue(sender, out var receivers))
{
    receivers.Remove(receiver);
    if (receivers.Count == 0) tree.LinksMap.Remove(sender);
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:42-45`

## Why a link is not purely constant

The map entry is constant, but the same link is also listed in the sender's `Targets` and the receiver's `Sources`, and in the tree's `Links`. Removing it from those lists is a linear `Contains`/`Remove`:

$$
T_{\text{link}} = O(1) + O(d) + O(L)
$$

A node's degree is a sum over its adjacency lists, so it is $O(S)$ rather than $O(1)$:

```csharp
foreach (var slot in node.Slots)
    degree += slot.Sources.Count;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:600-601`

## Traversal is the one place the model is asymptotically efficient

Breadth-first traversal marks visited nodes in a `HashSet`, so every node and every adjacency entry is examined once. That gives the standard bound:

$$
T_{\text{BFS}}(V,E) = O(V + E)
$$

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:275-281`

The contrast that matters in practice is lookup by container. The two-level map is constant; everything backed by a list is linear:

```plot
{
  "title": "Lookup cost by container",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "1", "color": "#4a9eff", "title": "LinksMap, index, degree" },
    { "fn": "x", "color": "#a78bfa", "title": "Contains / Remove on a list" },
    { "fn": "x*log(x+1)", "color": "#e5c07b", "title": "sorted work, for scale" }
  ]
}
```

## Memory

Per node the model stores the object plus one reference per slot; per slot one reference per incident link; per link four references (the map entry, the sender's `Targets` entry, the receiver's `Sources` entry, the tree's `Links` entry). That is $O(N + S + E + L)$ total, with no replication beyond the four link references. The tree also allocates one virtual link with two dummy slots unconditionally, which is a constant three objects per tree.
