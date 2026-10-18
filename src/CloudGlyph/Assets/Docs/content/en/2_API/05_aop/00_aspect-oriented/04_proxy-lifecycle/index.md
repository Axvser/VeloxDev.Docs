# AOP runtime — `Aop` & `AopCache`

Two static helpers behind the generated `Aop()` extension. `AopCache` returns one proxy per target instance; `Aop` maps a proxy back to its target. Both are weak in the direction that matters, so a proxy and its target are collected together.

## Type: `Aop` (static)

`Src/Core/VeloxDev.Core/AspectOriented/Aop.cs`:

```csharp
public static class Aop
{
    private static readonly ConditionalWeakTable<object, object> _proxyToTarget = [];

    public static void Map(object proxy, object target)
        => _proxyToTarget.Add(proxy, target);

    public static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class
        => _proxyToTarget.TryGetValue(proxy, out var t) ? (TTarget)t : null;
}
```

### Aop.Map

**Signature:** `void Map(object proxy, object target)`

| Parameter | Type | Description |
|---|---|---|
| `proxy` | `object` | The generated proxy |
| `target` | `object` | The instance it wraps |

**Returns:** `void`

**Exceptions:** none declared. `ConditionalWeakTable.Add` throws `ArgumentException` for a duplicate key; the generated factory calls `Map` once per created proxy, so this is not reachable through `Aop()`.

**Notes:** called by the generated `Aop()` factory immediately after constructing the proxy.

### Aop.GetTarget\<TTarget\>

**Signature:** `TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| Parameter | Type | Description |
|---|---|---|
| `proxy` | `IAspectOriented` | The proxy to reverse-map |

**Returns:** `TTarget?` — the target, or `null` when the proxy was never mapped.

**Exceptions:** none declared; an incompatible `TTarget` throws `InvalidCastException` on the cast.

**Notes:** amortized `O(1)`. Covered by `AopProxyTests.GetTargetReversesTheProxy`:

```csharp
Assert.AreSame(fixture, Aop.GetTarget<AopFixture>(fixture.Aop()));
```

## Type: `AopCache` (static)

`Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs`:

```csharp
private static class Entry<
    TClass,
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicParameterlessConstructor)] TInterface>
    where TClass : class
    where TInterface : class, IAspectOriented
{
    public static readonly ConditionalWeakTable<TClass, TInterface> Instances = [];
}

public static TInterface Resolve<
    TClass,
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicParameterlessConstructor)] TInterface>(
    TClass instance,
    Func<TClass, TInterface> factory)
    where TInterface : class, IAspectOriented
    where TClass : class
{
    return Entry<TClass, TInterface>.Instances
        .GetValue(instance, k => factory(k));
}
```

### AopCache.Resolve\<TClass, TInterface\>

**Signature:** `TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `TClass` | The target; the cache key |
| `factory` | `Func<TClass, TInterface>` | Constructs the proxy if none is cached |

**Returns:** `TInterface` — the cached proxy, or the factory result, which is then stored.

**Exceptions:** none declared. Exceptions from `factory` propagate and nothing is cached.

**Notes:**

- The nested generic `Entry<TClass, TInterface>` gives each `(TClass, TInterface)` pair its own `ConditionalWeakTable` through CLR generic specialization. No per-class cache code is generated.
- `ConditionalWeakTable.GetValue` is thread-safe: concurrent first calls may each run the factory, but exactly one result is stored and returned thereafter.
- The weak key is the target; the value keeps the proxy alive while the target is alive. The test `AProxyIsCollectableOnceItsTargetIs` asserts that dropping the target lets both be collected. There is no static registry rooting proxies.
- `TInterface` carries `DynamicallyAccessedMembers(PublicParameterlessConstructor)` solely to satisfy the trimmer's annotation on `ConditionalWeakTable`; `GetOrCreateValue` is never called. Concrete generated interfaces satisfy the annotation without a parameterless constructor.

Related pages: [ProxyEx](../02_proxyex/index.md) installs hooks on the returned proxy; [Generated API](../../01_generated-api/index.md) shows the `Aop()` extension that calls `Resolve`.
