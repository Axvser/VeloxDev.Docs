# Complexity Analysis — AOP

## Proxy cache lookup (`AopCache.Resolve`)

$$O(1) \text{ amortized per } \text{Aop()}$$

`AopCache.Resolve` is a single `ConditionalWeakTable<TClass, TInterface>.GetValue` call (`AopCache.cs` lines 24-32). `ConditionalWeakTable` is a CLR hashtable with weak keys, so the get-or-create lookup is amortized $O(1)$ and the proxy is created **once per target instance** — every later `Aop()` call is a cache hit.

$$T_{\text{Aop()}} = O(1) \text{ amortized}$$

## Dispatch + hook lookup (`ProxyInstance.Invoke`)

$$O(1) \text{ per dispatch, } + O(h) \text{ hook handlers}, \quad h \le 3$$

`Invoke` normalizes the member name once, then resolves the hook triple with a `Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>>` lookup (`GetterActions` / `SetterActions` / `MethodActions` — `ProxyInstance.cs` lines 19-21, 29-31). Dictionary access is amortized $O(1)$; the member name is already normalized (`get_*` / `set_*` prefix) by the `DispatchProxy` dispatch.

Each intercepted call then pays the cost of the active hooks — at most three handlers (start, coverage, end):

$$T_{\text{intercept}} = O(1) + O(h), \quad h \le 3$$

## Reflection fallback path (`coverage == null`)

When `coverage == null`, `Invoke` reflects into the real target:

```csharp
_targetType?.GetMethod(Name)?.Invoke(_target, args)
```

`Type.GetMethod(string)` performs a linear scan over the type's metadata, and `MethodInfo.Invoke` boxes arguments:

$$O(m) \text{ lookup } + O(a) \text{ invoke}, \quad m = \text{members in type}, \ a = \text{argument count}$$

The reflection fallback is therefore strictly more expensive than a `coverage` handler. *This cost characterization is inferred from the `GetMethod` / `Invoke` usage at `ProxyInstance.cs` line 33; the underlying algorithms are standard BCL behavior.*

## Reverse lookup (`Aop.GetTarget`)

$$O(1) \text{ amortized}$$

`Aop.GetTarget<TTarget>` is a `ConditionalWeakTable<object, object>.TryGetValue` reverse lookup (`Aop.cs` lines 19-26) — amortized $O(1)$, independent of the number of mapped proxies.

## Memory behavior (weak tables)

| Structure | Memory behavior |
|---|---|
| `AopCache.Entry<TClass,TInterface>` | One `ConditionalWeakTable` per `(TClass, TInterface)` pair via CLR generic specialization — **weak keys**, so a proxy is collected together with its target; no per-class cache code is generated |
| `Aop._proxyToTarget` | One `ConditionalWeakTable<object, object>` for proxy → target reverse mapping — weak keys, does not root proxies |
| `ProxyInstance.ProxyInstances` | `Dictionary<Guid, ProxyInstance>` — **strong** static registry; entries are removed by the `ProxyInstance` constructor lifecycle only, so proxies referenced here are not collected while registered |
| `ProxyInstance.ProxyIDs` | `Dictionary<object, Guid>` — **strong** reference from proxy → `Guid`; pairs with `ProxyInstances` for `SetProxy` resolution |
| Hook tables | `O(k)` `Dictionary` entries per `ProxyInstance`, where `k` = number of distinct members with registered hooks |

> Note: the static `ProxyInstances` / `ProxyIDs` dictionaries are strong references and grow with every proxy that is registered and not removed. For long-lived applications that create many targets, an unreleased proxy registered in these tables cannot be reclaimed. The per-pair `AopCache` table and `Aop._proxyToTarget` are weak, so they are not retention hazards.

## Per-operation summary

| Operation | Complexity |
|---|---|
| `Aop()` proxy resolve (`AopCache.Resolve`) | $O(1)$ amortized |
| `ProxyInstance.Invoke` dispatch | $O(1)$ amortized (dictionary lookup) |
| Hook execution | $O(h)$, $h \le 3$ |
| Intercepted call total | $O(1) + O(h)$, $h \le 3$ |
| Reflection fallback (`coverage == null`) | $O(m) + O(a)$ |
| `Aop.GetTarget` reverse lookup | $O(1)$ amortized (CWT) |
| Memory (proxy cache) | Weak per-pair table — proxy dies with target |
| Memory (static registries) | Strong `ProxyInstances` / `ProxyIDs` — grow with registered proxies |

> Source references: `Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyInstance}.cs`.
