# Complexity Analysis — AOP, MonoBehaviour & WeakTypes

## AOP

### Hook lookup

$$O(1)$$

`ProxyInstance.Invoke` resolves the hook triple with a `Dictionary<string, Tuple<...>>` lookup on the member name (`GetterActions` / `SetterActions` / `MethodActions`). Dictionary access is amortized $O(1)$; the member name is already normalized (`get_*` / `set_*` prefix) by the generated proxy.

### DispatchProxy invocation

$$O(1) \text{ per call, } + O(h) \text{ hook handlers}$$

Each intercepted call pays a constant overhead for the dispatch + lookup, plus $O(h)$ for the active hooks where $h \le 3$ (start, coverage/end). So a fully-wrapped member costs:

$$T_{\text{intercept}} = O(1) + O(h), \quad h \le 3$$

### Reflection fallback path

When `coverage == null`, `Invoke` reflects into the real target:

```csharp
_targetType?.GetMethod(Name)?.Invoke(_target, args)
```

`GetMethod(string)` is a linear scan over the type's metadata and `MethodInfo.Invoke` boxes arguments:

$$O(m) \text{ lookup } + O(a) \text{ invoke, } \quad m = \text{members in type}, \ a = \text{argument count}$$

The reflection fallback is therefore strictly more expensive than a coverage handler. *This cost characterization is inferred from the `GetMethod`/`Invoke` usage at `ProxyInstance.cs` line 33; the algorithm is standard BCL behavior.*

### Proxy cache

$$O(1) \text{ amortized per } \text{Aop()}$$

`AopCache.Resolve` is a `ConditionalWeakTable.GetValue` — amortized $O(1)$; the proxy is created once per target and collected with it.

## MonoBehaviour

### Per-frame update

$$O(b), \quad b = \text{active behaviors}$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` iterate the cached wrapper array once, calling `InvokeUpdate` / `InvokeLateUpdate` per behavior (stopping early when `e.Handled == true` or the token is cancelled) — `MonoBehaviourManager.cs` lines 610-640. The array is rebuilt only when behaviours are added/removed or every `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms, so the per-frame sort cost is amortized away.

At target FPS:

$$T_{\text{update}} = O(b) \text{ per frame, } \quad \frac{1}{FPS} \le 1000 \text{ ms}, \ FPS \in [1, 1000]$$

### Fixed update

$$O(b) \text{ every } \approx 16 \text{ ms}$$

`ExecuteBehaviorsFixedUpdateSync` runs on the fixed thread each `SetFixedUpdateInterval` ms (default `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`), so the steady-state cost is $O(b)$ per 16 ms regardless of frame rate.

### Frame pacing

Sleep is `PrecisionSleep` (spins below `SPIN_ONLY_THRESHOLD_MS = 2` ms, otherwise `Thread.Sleep(1)` + tail spin) — `MonoBehaviourManager.cs` lines 777-802. It is $O(1)$ wall-clock per frame.

## WeakTypes

### WeakQueue / WeakStack

$$\text{Enqueue / Push: } O(1), \quad \text{TryDequeue / TryPop: } O(1) \text{ amortized}$$

Each mutation is a lock-guarded `Queue`/`Stack` operation on a `WeakReference<T>`. `TryDequeue`/`TryPop` skip collected references in a loop:

$$O(1 + d) \text{ amortized}, \quad d = \text{dead references at the front}$$

`Count`, `GetEnumerator`, and `TrimExcess` first prune the whole structure:

$$O(n), \quad n = \text{stored references}$$

so the worst case for `Count`/enumeration is $O(n)$, while the common mutation path stays amortized $O(1)$.

### WeakCache

$$O(1) \text{ amortized}$$

`AddOrUpdate` / `TryGetCache` / `Remove` are `ConditionalWeakTable` operations plus a list insert/scan. Cleanup is periodic, triggered when an insert counter exceeds the adaptive threshold (`_perceptionThreshold = 4`, doubling per sweep — `WeakCache.cs` lines 12, 44-62):

$$\text{sweep: } O(n) \text{ worst-case}, \quad \text{amortized } O(1) \text{ per insert}$$

### Memory

| Structure | Behavior |
|---|---|
| `ProxyInstance` hooks | $O(\text{members})$ dictionaries; proxy lives in `ConditionalWeakTable` → collected with target |
| `WeakDelegate` | $O(h)$ `WeakReference<Delegate>`; **no strong reference** to subscribers |
| `WeakQueue` / `WeakStack` | $O(n)$ weak refs; dead refs pruned on access, entries do not root the objects |
| `WeakCache` | `ConditionalWeakTable` + $O(n)$ sweep list; keys do not keep values alive beyond table semantics |

The defining property is that **weak references avoid retention**: a subscriber, queue item, or cache key that becomes unreachable elsewhere can be collected, which is exactly the leak-avoidance these types exist for.

## Per-operation summary

| Operation | Complexity |
|---|---|
| AOP hook lookup | $O(1)$ |
| AOP intercepted call | $O(1) + O(h)$, $h \le 3$ |
| AOP reflection fallback | $O(m) + O(a)$ |
| `Aop()` proxy resolve | $O(1)$ amortized |
| MonoBehaviour update (per frame) | $O(b)$ |
| MonoBehaviour fixed update | $O(b)$ per ~16 ms |
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | $O(1)$ amortized |
| `WeakQueue.Count` / enumeration | $O(n)$ worst-case (prune) |
| `WeakCache.AddOrUpdate` / `TryGetCache` | $O(1)$ amortized |
| `WeakCache` periodic sweep | $O(n)$ worst-case |
