# Dynamic slot enumeration

`SlotEnumerator<TSlot>` keeps a `Dictionary<object, TSlot>` from selector value to slot, so selecting a running value is constant-time. The cost is in *changing* the selector: the old branch set is torn down, the new one materialised, and links are reconnected branch by branch. That reconnection is the only super-linear step, and it is quadratic when branches are matched by name.

Notation: $E$ enum members or provider definitions, $E_{\text{prev}}$ branches in the previous set, $d$ degree, $L$ tree links, $S$ slots on the owning node, $P$ providers, $R$ deferred removals.

## Cost model

| Operation | Time | Source |
|---|---|---|
| `TrySelect` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:279` |
| `SetSelector`, enum, fresh build | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:285` |
| `SetSelector`, provider, fresh build | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:300` |
| `SetSelector`, cached type | $O(1)$ lookup + $O(E+L)$ apply | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:401` |
| Pre-switch wiring snapshot | $O(E d + L)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:372` |
| `ApplyAttachedState` | $O(L + E + E S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:551` |
| `ApplyNewState` reconnection | $O(E^2)$ by name | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:439` |
| Bulk add of $n$ items | $O(n^2)$ worst | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:96` |
| `FlushDeferredRemovals` | $O(R n)$ amortized | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:260` |
| `Install` / `Uninstall` | $O(P)$ / $O(E+P)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:675` |

The routing lookup is a single dictionary probe:

```csharp
public bool TrySelect(object value, out TSlot? slot)
{
    return conditionMap.TryGetValue(value, out slot);
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:279-282`

## Rebuilding the branch set

`SetSelector` captures the current wiring first — each item's `Targets` and `Sources` arrays, plus the subset of tree links that touch the current slots. That snapshot is linear in branches times degree plus tree links. It then swaps items and reconnects each new branch to the neighbours of the branch it replaces:

```csharp
for (int i = 0; i < state.Items.Count; i++)
{
    var branch = state.Items[i].Slot;
    var previous = MatchBranch(previousWiring, state.Items[i].Name, i, byName);
    ...
    foreach (var receiver in previous.Value.Targets)
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:439-445`

`MatchBranch` is a linear search over the previous set when matching by name (same selector type), and an index lookup when matching by position (different type). Matching by name makes the whole reconnection step quadratic:

$$
T_{\text{apply}}(E) = O(E^2 + E\,d + L)
$$

```plot
{
  "title": "Branch reconnection: by position vs by name",
  "grid": true,
  "xAxis": { "domain": [0, 60] },
  "yAxis": { "domain": [0, 3600] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "match by position, O(E)" },
    { "fn": "x*x", "color": "#f472b6", "title": "match by name, O(E^2)" }
  ]
}
```

## Duplicate values and deferred removal

Adding an item checks the value map in $O(1)$ but then scans `Items` to find a stale duplicate, which is $O(E)$ per add and $O(n^2)$ for a bulk add. Removing items during a collection-changed callback is deferred to a list and flushed lazily; each flush is linear in the current item count.

## Memory

Each branch normally costs one `ConditionalSlot<TSlot>` plus one `TSlot`. On the provider path the enumerator allocates **two** slots per definition — `ConditionalSlot` eagerly constructs one, and `SetSelector` overwrites it with a newly constructed slot. The larger retention is the per-type state cache: `_typeStates` keeps a full `SelectorState` (items and link array) for every selector type ever used, with no eviction, so memory is $O(\sum_E \text{items} + \sum_E \text{links})$ for the lifetime of the enumerator. The deferred-removal list is transient.
