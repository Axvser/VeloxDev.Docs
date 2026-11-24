# Aspect-oriented programming

The proxy is generated C#: one class per target type with one hook field per interceptable member and a fixed `switch` over member keys. Calls are typed virtual calls, not reflection. The per-call cost is therefore a field read plus an optional delegate chain, and the per-instance cost is one proxy with $M$ reference-sized hook slots.

Notation: $M$ interceptable members on a type, $n$ arguments on a hooked call, $k$ installed hooks (at most three per member).

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `AopCache.Resolve` | $O(1)$ avg weak-table lookup | $O(1)$ table entry | `Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs:41` |
| Proxy creation (first resolve) | $O(M)$ field initialisation | $O(M)$ per proxy | `Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs:58` |
| `Aop.Map` / `Aop.GetTarget` | $O(1)$ avg | $O(1)$ per pair | `Src/Core/VeloxDev.Core/AspectOriented/Aop.cs:19` |
| `SetProxy` | $O(1)$ switch + key hash | one `AspectHooks` | `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs:50` |
| Unhooked member call | $O(1)$, no allocation | — | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:251` |
| Hooked getter | $O(1)$ up to 3 delegates + boxing | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:257` |
| Hooked method | $O(1)$ delegate calls + $O(n)$ array/boxing | $O(n)$ | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:310` |

## Resolution is a weak table, not a cache walk

Each closed `(TClass, TInterface)` pair gets its own static `ConditionalWeakTable`, so resolution is a hash lookup and the factory runs only on a miss:

```csharp
return Entry<TClass, TInterface>.Instances
    .GetValue(instance, k => factory(k));
```

Source: `Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs:49-50`

`Aop.Map` and `Aop.GetTarget` are two more weak-table operations, one per direction. Both tables are keyed weakly, so a proxy and its target become collectable together without explicit removal.

## The fast path has no reflection

Generated getters read the hook field and, when it is null, call the target directly:

```csharp
if (_hooks_get_Name is null)
    return _target.Name;
```

Source: `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:251-255` (shape)

When hooks are installed, the call becomes up to three delegate invocations plus the underlying access:

```csharp
var start = _hooks_get_Name?.Start;
var coverage = _hooks_get_Name?.Coverage;
var end = _hooks_get_Name?.End;
start?.Invoke(...);
var value = coverage is null ? _target.Name : coverage(...);
end?.Invoke(...);
return value;
```

Source: `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:257-262` (shape)

A hooked method with $n$ value-type arguments allocates an `object[]` and boxes each argument; a computed property's result is boxed as well. With no hooks, neither happens.

## Hook installation is a generated switch

`SetProxy` builds the key (`get_`/`set_` plus the member name) and hands the hooks to the proxy, whose generated `SetHooks` is a `switch` over constant strings:

```csharp
public void SetHooks(string memberKey, AspectHooks? hooks)
{
    switch (memberKey)
    {
        case "get_Name": _hooks_get_Name = hooks; break;
        ...
        default: throw new ArgumentOutOfRangeException(nameof(memberKey));
    }
}
```

Source: `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:336-361` (shape)

For a fixed member set this is $O(1)$ after the string hash. Installing replaces the whole `AspectHooks` value rather than merging individual hooks.

## Availability and memory

The AOP runtime is inside `#if NET`, so it is compiled into `net5.0` and `net8.0` builds but not into `netstandard2.0` or `netframework4.6.1`. That is a precondition for every cost above: on the older targets the proxy type does not exist.

Memory per proxy is one target reference plus one hook reference per interceptable member; an installed `AspectHooks` is three delegate references. Two weak-table entries per live proxy (instance to proxy, proxy to instance) are reclaimable by the GC, and the static generic tables hold no strong entries.
