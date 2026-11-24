# Workflow Agent Tools

Every tool in `WorkflowAgentToolkit` works against the live tree, so its cost is a function of graph size, not of the prompt. The dominant term is not the traversal itself but the metadata walk each tool performs per object: `AppendScalarProperties` re-reads the type's recorded member list — including inherited members — for every node on every call. Bounds are read from the cited control flow; where a helper's internals lie outside the cited module, the bound is inferred.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | nodes in the tree |
| $m$ | links in the tree |
| $s$ | slots of one node |
| $p$ | recorded properties of one type, inherited members included |
| $k$ | nodes returned by a traversal |
| $q$ | keys in one patch document |
| $T$ | tools built for a category mask |

`p` is not memoised. `PropertiesOf` resolves the accessor on each object and walks `AIContextDirectory.Shared.MembersAcross(TypeName, "Properties")` again, so a read that looks linear in nodes is linear in node-members.

## Tool construction

`CreateAllTools` fills a list through a local `Add(category, items)` that tests `(categories & category) == category`, a constant-time bitwise check per tool block (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs:88-99`).

```csharp
AITool T(Delegate method, string name, AgentActionCategory action)
    => new TrackedAIFunction(AIFunctionFactory.Create(method, name), Tools, _scope.Pipeline, action);

var tools = new List<AITool>();

void Add(WorkflowToolCategory category, params AITool[] items)
{
    if ((categories & category) == category)
        tools.AddRange(items);
}
```

Construction is $O(T)$ list work plus one `AIFunctionFactory.Create` per tool. A second pass filters by `_scope.IsToolEnabled`, a hash-set lookup. `ResetToolCallLimit` is added outside every category block, so narrowing the mask cannot remove it.

## Read and query tools

| Operation | Time | Space |
|---|---|---|
| `ListNodes` | $O(n \cdot p)$ | $O(n)$ JSON |
| `GetNodeDetail` | $O(p + s + \text{targets})$ | $O(p + s)$ |
| `ListConnections` | $O(m)$ scan, then $O(m)$ `Skip/Take` | $O(m)$ |
| `GetFullTopology` | $O(n \cdot (p+s) + m)$ | $O(n + m)$ |
| `FindNodes` | $O(n \cdot p)$ | $O(k)$ output |
| `FindComponentById` | $O(n \cdot (p+s) + m)$ | $O(n)$ transient dictionaries |
| `FindNodeById`, `IndexOfNode` | $O(n)$ | $O(1)$ |

`ListConnections` scans every link and then materialises the match list before paginating, so `skip`/`take` reduce output, not work (`WorkflowAgentToolkit.cs:742-805`). `FindComponentById` builds a slot-property map for every node before it can answer, which is the cost every `*ById` tool inherits (`WorkflowAgentToolkit.cs:3480-3502`).

## Traversal versus reporting

The BFS itself is linear. `FindPath` uses a parent map and a queue, $O(n+m)$ time and $O(n)$ space (`WorkflowAgentToolkit.cs:1880-1929`). The reporting wrapper destroys that bound: `BuildNodeListResult` asks `IndexOfNode` for each result, and `IndexOfNode` is a linear scan of `Tree.Nodes` (`WorkflowAgentToolkit.cs:1931-1944`, `:3460-3465`).

```csharp
private string BuildNodeListResult(IEnumerable<INodeComponent> nodes)
{
    var arr = new VeloxJsonArray();
    foreach (var n in nodes)
    {
        arr.Add(new VeloxJsonObject
        {
            ["i"] = IndexOfNode(n),
            ["id"] = GetComponentId(n),
            ["t"] = n.GetType().Name,
        });
    }
    return arr.ToJson();
}
```

For a traversal that returns $k$ nodes the reported cost is

$$
T_{\text{report}} = O(k \cdot n)
$$

and path reconstruction adds $O(L_{\text{path}} \cdot n)$. The graph walk is not the bottleneck; indexing the answer is.

```plot
{
  "title": "Traversal vs. indexed reporting",
  "grid": true,
  "xAxis": { "domain": [1, 200] },
  "yAxis": { "domain": [0, 40000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "BFS: n" },
    { "fn": "x*ln(x)", "color": "#a78bfa", "title": "n log n" },
    { "fn": "x^2", "color": "#f472b6", "title": "k = n reporting" }
  ]
}
```

## Patch, schema and validation

`ComponentPatcher.ApplyPatch` handles each patch key with one member lookup, a framework-managed-property set test, a backing-command probe, conversion to the declared type and an equality check before writing (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ComponentPatcher.cs:76-90`). For $q$ keys and $p$ members:

$$
T_{\text{patch}} = O(q \cdot (p + b))
$$

where $b$ is the backing-command discovery cost. The patch document is fully materialised before any cap applies, so the result-size cap bounds tokens, not peak memory.

`TypeIntrospector.GetTypeSchema` is more expensive than metadata alone suggests: it resolves references, walks `MembersAcross`, loops every language, and constructs and serialises a default instance (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/TypeIntrospector.cs:106-120`).

`ValidateWorkflow` performs one node pass with slot and property scans, builds an adjacency map, then runs a recursive three-colour DFS for cycles (`WorkflowAgentToolkit.cs:2968-3101`). Time is $O(n \cdot (p+s) + m + \sum \text{validators})$; stack depth equals the longest acyclic path, so a pathological graph can overflow.

## Selection and snapshot state

`WorkflowAgentSelection.Add` copies the current arrays, then tests each incoming node with `ContainsReference`, a linear scan (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentSelection.cs:109-123`, `:446-452`). Adding $a$ nodes to a set of $s$ is

$$
T_{\text{add}} = O(a \cdot (s+a))
$$

and select-all is the worst case, $O(a^2)$. `Render` caps output at 64 rows, which bounds the prompt, not the update.

`WorkflowStateTracker.GetChangesSinceLastSnapshot` always calls `BuildSnapshot()` first, even when nothing changed; there is no dirty flag and no reuse of the previous object (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs:42-56`). A diff costs at least a full snapshot:

$$
T_{\text{diff}} = O(n \cdot (p+s) + m + \text{chars})
$$

## Context envelope and caching

The per-turn envelope is cached on a packed `ContextKey` of version, selection revision and usage band, read in constant time (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2106-2116`). On a key hit the provider returns the same `AIContext` instance with no lock and no allocation (`Agent/Workflow/WorkflowAgentContextProvider.cs:86-110`). On a miss, rendering is $O(g \log g + \text{disabled} \log \text{disabled} + r + T + \text{chars})$: rule lists and tool switches are snapshotted and sorted, budgets are constant-time, and only drifted sections are re-emitted.

## Related

- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — the per-call gate these tools pass through.
- [MCP Integration](../20_mcp-integration/index.md) — external tools joining the same per-turn tool array.
- [Sub-Agents](../21_sub-agents/index.md) — children that inherit this toolkit under a smaller ledger.
