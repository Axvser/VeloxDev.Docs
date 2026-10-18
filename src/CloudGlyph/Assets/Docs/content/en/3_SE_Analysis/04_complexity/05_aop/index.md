# Complexity Analysis — AOP

The hot paths are the cache lookup in `Aop()`, the per-call branch in the generated proxy, and the hook pipeline. Because the proxy is generated C#, there is no reflection stage to price in: the previous design's `Type.GetMethod` + `MethodInfo.Invoke` cost is gone entirely.

## Proxy resolution — `AopCache.Resolve`

$$
T_{\text{Aop()}} = O(1) \text{ amortized}
$$

`AopCache.Resolve` is one `ConditionalWeakTable<TClass, TInterface>.GetValue` call (`AopCache.cs`). `ConditionalWeakTable` is a CLR hash table with weak keys, so hit and miss are amortized $O(1)$. The first call for a target pays the factory once:

$$
T_{\text{first}} = O(1) \text{ construction} + O(1) \text{ CWT insert} + O(1) \text{ reverse-map insert}
$$

`new {Interface}Proxy(target)` allocates one object with one `_target` field plus one `AspectHooks?` field per interceptable accessor. There is no type generation at runtime, so unlike `DispatchProxy` there is no first-use `Reflection.Emit` cost per interface.

## Hook installation — `ProxyEx.SetProxy`

$$
T_{\text{SetProxy}} = O(1)
$$

The method performs two type/identity checks, builds a short string (`get_` / `set_` prefix or none), allocates one `AspectHooks`, and executes one `switch` case. Re-installation overwrites the field; there is no list traversal and no dictionary.

## Intercepted call

### No hooks (the common case)

$$
T_{\text{call}} = O(1) + O(a)
$$

where $a$ is the argument-evaluation cost of the call itself. The generated fast path is:

```csharp
var h = _hooks_Add;
if (h is null)
{
    return _target.Add(a, b);
}
```

No array, no boxing, no delegate invocation, no lookup. This is the path for every member that was never registered.

### With hooks

$$
T_{\text{hooked}} = O(1) + O(a) + O(h), \quad h \le 3
$$

- One `_hooks_*` field read.
- Argument boxing into `object?[]` — methods with parameters and setters allocate one array; getters and parameterless methods pass `null` and allocate nothing.
- Up to three delegate invocations (`Start`, `Coverage`, `End`).
- One unboxing cast on the return path for value-type members.

`Coverage == null` does not add a stage; it runs the body in place of the delegate call. `End` is invoked even when the body is `void` (with `r1 == null`).

### Compare with the removed reflection path

The old design's fallback was:

$$
O(m) \text{ metadata scan} + O(a) \text{ boxing} + O(a) \text{ argument array}
$$

for `Type.GetMethod(name)` and `MethodInfo.Invoke`, on **every** call. The generated path replaces the $O(m)$ scan with a direct call and also removes the `TargetInvocationException` wrapper on target exceptions.

## Proxy-to-target lookup — `Aop.GetTarget`

$$
O(1) \text{ amortized}
$$

One `ConditionalWeakTable<object, object>.TryGetValue`. Independent of the number of mapped proxies.

## Memory

| Structure | Behavior |
|---|---|
| `AopCache.Entry<TClass,TInterface>.Instances` | One `ConditionalWeakTable` per `(TClass, TInterface)` pair via generic specialization. Weak key = target, strong value = proxy. One entry per live proxied target. |
| Proxy instance | $O(m)$ where $m$ = number of interceptable accessors: `_target` plus one `AspectHooks?` field each. Unhooked members hold `null`. |
| `AspectHooks` | Three delegate references per installed set; replaced, never accumulated. |
| `Aop._proxyToTarget` | One `ConditionalWeakTable<object, object>`: weak key = proxy, strong value = target. |

**Retention.** There are **no static strong registries**. `AopCache` keeps the proxy alive only while the target is reachable, and `Aop` keys on the proxy. Once the target becomes unreachable, the proxy and the reverse entry become collectable together — the ephemeron semantics of `ConditionalWeakTable` handle the target → proxy → target cycle. This is asserted by `AProxyIsCollectableOnceItsTargetIs`:

```csharp
Assert.IsFalse(target.IsAlive, "nothing outside the proxy may root the target");
Assert.IsFalse(proxy.IsAlive, "and no static registry may root the proxy");
```

Memory therefore grows with the number of **live** proxied targets, not with the number ever created.

**Trimming.** The generated proxy contains no reflection, and `AopCache`'s `DynamicallyAccessedMembers` annotation on `TInterface` exists only to satisfy the trimmer's requirement on `ConditionalWeakTable`; `GetOrCreateValue` is never called.

## Per-operation summary

| Operation | Time | Allocation |
|---|---|---|
| `Aop()` — cached | $O(1)$ amortized | none |
| `Aop()` — first call | $O(1)$ | one proxy, one CWT entry, one weak map entry |
| `SetProxy` | $O(1)$ | one `AspectHooks` |
| Unhooked member call | $O(1) + O(a)$ | none beyond the call itself |
| Hooked getter | $O(1) + O(h)$ | none for arguments |
| Hooked setter / parameterised method | $O(1) + O(a) + O(h)$ | one `object?[]` |
| `Aop.GetTarget` | $O(1)$ amortized | none |

> Source: `Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyEx,AspectHooks}.cs`, `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`, `Src/Core/VeloxDev.Core.Test/AspectOriented/AopProxyTests.cs`.
