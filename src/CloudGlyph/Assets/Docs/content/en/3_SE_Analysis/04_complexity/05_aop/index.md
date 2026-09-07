# Complexity Analysis — AOP

The AOP hot paths are the proxy cache lookup (`AopCache.Resolve`), the per-call dispatch (`ProxyInstance.Invoke`), and the `coverage == null` reflection fallback. Constants below assume one `Aop()` proxy per target instance, which is what the per-pair `ConditionalWeakTable` guarantees.

## Proxy resolution (`AopCache.Resolve` / `Aop()`)

$$
O(1) \text{ amortized per } Aop()
$$

`AopCache.Resolve` is a single `ConditionalWeakTable<TClass, TInterface>.GetValue` call (`AopCache.cs`, lines 24-32, table declared at 14-19). `ConditionalWeakTable` is a CLR hash table with weak keys, so the get-or-create lookup is amortized $O(1)$:

$$
T_{\text{Aop()}} = O(1) \text{ amortized}
$$

The first call for a given target pays the factory cost once — `ProxyEx.CreateProxy` runs `DispatchProxy.Create<T, ProxyInstance>()` (`ProxyEx.cs`, lines 17-25), which allocates the instance and registers it in the static `ProxyIDs` map. (`DispatchProxy` generates and caches the concrete proxy *type* only once for the whole `(interface, ProxyInstance)` pair, so later targets skip that.) Every later `Aop()` for that target is a pure cache hit. Because one proxy is created per target instance, the per-instance creation cost is $O(1)$ amortized over that instance's lifetime.

## Dispatch + hook lookup (`ProxyInstance.Invoke`)

$$
O(1) \text{ per dispatch} \;+\; O(h) \text{ hook handlers},\quad h \le 3
$$

`Invoke` computes the member name once (`ProxyInstance.cs`, line 25), selects one of three dictionaries by its `get_*` / `set_*` prefix (lines 29-52), and resolves the hook triple with a `Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>>` lookup (`GetterActions` / `SetterActions` / `MethodActions`, declared at lines 19-21). Dictionary access is amortized $O(1)$; the dispatch itself does no reflection.

Each intercepted call then pays the cost of the active hooks — at most three handlers (`start`, `coverage`, `end`):

$$
T_{\text{intercept}} = O(1) + O(h),\quad h \le 3
$$

## Reflection fallback path (`coverage == null`)

When no `coverage` handler is registered (including members with no hooks at all), `Invoke` reflects into the real target:

```csharp
// Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs (method branch, line 49)
var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
```

`Type.GetMethod(string)` scans the type's metadata linearly, and `MethodInfo.Invoke` boxes the arguments:

$$
O(m) \text{ lookup} + O(a) \text{ invoke},\quad m = \text{members in type},\; a = \text{argument count}
$$

The reflection fallback is therefore strictly more expensive than a `coverage` handler and is the dominant per-call cost for unhooked members. *This characterization follows from the `GetMethod`/`Invoke` call at `ProxyInstance.cs` line 49; the underlying algorithms are standard BCL behavior.*

## Reverse lookup (`Aop.GetTarget`)

$$
O(1) \text{ amortized}
$$

`Aop.GetTarget<TTarget>` is a `ConditionalWeakTable<object, object>.TryGetValue` reverse lookup (`Aop.cs`, lines 13, 25-26) — amortized $O(1)$, independent of the number of mapped proxies.

## Memory behavior

| Structure | Memory behavior |
|---|---|
| `AopCache.Entry<TClass,TInterface>.Instances` | One `ConditionalWeakTable<TClass, TInterface>` per `(TClass, TInterface)` pair via CLR generic specialization — weak key (the target), strong value (the proxy). One cached entry per proxied target |
| `Aop._proxyToTarget` | One `ConditionalWeakTable<object, object>` for proxy → target reverse mapping — weak key, strong value |
| `ProxyInstance.ProxyInstances` | `Dictionary<Guid, ProxyInstance>` — **static strong** registry; each created `ProxyInstance` is added in its constructor (line 13) |
| `ProxyInstance.ProxyIDs` | `Dictionary<object, Guid>` — **static strong** proxy → `Guid` map, populated by `ProxyEx.CreateProxy` (line 23) |
| Hook dictionaries | Three `Dictionary<string, Tuple<...>>` per `ProxyInstance` — $O(k)$ entries where $k$ = number of distinct members registered with hooks; empty maps cost $O(1)$ each |

**Retention note.** Both static registries only ever grow: entries are added on proxy creation and there is no removal/unregister API. Because a `ProxyInstance` is strongly referenced from `ProxyInstances`/`ProxyIDs`, and it in turn holds a strong `_target` reference (`ProxyInstance.cs`, line 15), **neither the proxy nor its target can be reclaimed once `Aop()` has been called for that instance** — even when the application drops all other references. The per-pair `AopCache` weak table and `Aop._proxyToTarget` are weak at the key, but they cannot reclaim a proxy that the static registries keep alive. For long-lived processes that proxy many distinct instances, memory grows linearly with the number of distinct proxied targets. An un-hooked member costs nothing extra, but the empty hook dictionaries still exist per instance.

## Per-operation summary

| Operation | Complexity |
|---|---|
| `Aop()` proxy resolve (`AopCache.Resolve`) | $O(1)$ amortized |
| Proxy creation (`DispatchProxy.Create`) | one-time type generation per `(interface, ProxyInstance)` pair; one instance allocation + registration per target |
| `ProxyInstance.Invoke` dispatch | $O(1)$ amortized (dictionary lookup + prefix check) |
| Hook execution | $O(h)$, $h \le 3$ |
| Intercepted call total | $O(1) + O(h)$, $h \le 3$ |
| Reflection fallback (`coverage == null`) | $O(m) + O(a)$ |
| `Aop.GetTarget` reverse lookup | $O(1)$ amortized (CWT) |
| Memory (per-pair proxy cache) | $O(1)$ per proxied target; keys weak, but static registries root proxy + target |
| Memory (static registries) | Strong `ProxyInstances` / `ProxyIDs` — grow with every distinct proxied target, never reclaimed |

> Source references: `Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyInstance,ProxyEx}.cs`.
