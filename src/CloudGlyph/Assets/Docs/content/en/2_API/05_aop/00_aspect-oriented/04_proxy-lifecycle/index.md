# AOP runtime — `Aop` & `AopCache`

The lifecycle helpers behind the generated `Aop()` entry point. `Aop` keeps the proxy-to-target reverse map (for unwrapping a proxy back to the original instance); `AopCache` caches one proxy per target instance so `Aop()` returns a stable proxy.

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
| `proxy` | `object` | The AOP proxy |
| `target` | `object` | The original instance the proxy wraps |

**Returns:** `void`

**Exceptions:** none declared (a duplicate key throws `ArgumentException`, but `Aop()` registers each proxy once through `AopCache`).

**Notes:** adds `proxy → target` to a static `ConditionalWeakTable<object, object>`. Called by the generated `Aop()` extension right after `ProxyEx.CreateProxy`. The weak table keeps the proxy alive only as long as the target.

### Aop.GetTarget\<TTarget\>

**Signature:** `TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| Parameter | Type | Description |
|---|---|---|
| `proxy` | `IAspectOriented` | The AOP proxy to reverse-map |

**Returns:** `TTarget?` — the original target instance, or `null` if the proxy was never mapped.

**Exceptions:** none.

**Notes:** reverse lookup on the same `ConditionalWeakTable` — amortized `O(1)`. The signature is inferred from the runtime source (no demo/test exercises it); a natural use is `var original = Aop.GetTarget<TeamViewModel>(team);`.

## Type: `AopCache` (static)

`Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs`:

```csharp
public static class AopCache
{
    private static class Entry<TClass, TInterface>
        where TClass : class
        where TInterface : class, IAspectOriented
    {
        public static readonly ConditionalWeakTable<TClass, TInterface> Instances = [];
    }

    public static TInterface Resolve<TClass, TInterface>(
        TClass instance,
        Func<TClass, TInterface> factory)
        where TInterface : class, IAspectOriented
        where TClass : class
    {
        return Entry<TClass, TInterface>.Instances
            .GetValue(instance, k => factory(k));
    }
}
```

### AopCache.Resolve\<TClass, TInterface\>

**Signature:** `TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `TClass` | The target instance keying the cache |
| `factory` | `Func<TClass, TInterface>` | Creates the proxy when `instance` has no cached proxy yet |

**Returns:** `TInterface` — the cached proxy if one exists, otherwise the `factory` result, which is then stored.

**Exceptions:** none declared.

**Notes:**

- Each `(TClass, TInterface)` pair gets its own `ConditionalWeakTable<TClass, TInterface>` through the nested generic `Entry<TClass, TInterface>` (CLR generic specialization) — no per-class cache code is needed.
- Uses `ConditionalWeakTable.GetValue` semantics: the factory runs at most once per instance, and the entry lives as long as the instance (weak keys), so the proxy is garbage-collected together with its target.
- This is what makes repeated `_teamData.Aop()` calls return the same proxy (`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`).

Related pages: [ProxyEx](../02_proxyex/index.md) provides the `factory`'s internals; the generated `Aop()` that calls `Resolve` is described in [Generated API](../../01_generated-api/index.md).
