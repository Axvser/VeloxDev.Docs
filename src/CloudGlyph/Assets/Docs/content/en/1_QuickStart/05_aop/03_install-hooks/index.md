# Install Hooks

## Get the proxy

```csharp
var proxy = counter.Aop();
```

`Aop()` is generated per target class. It calls `AopCache.Resolve<Counter, Counter_AopQuickStart_Aop>(instance, factory)`, so repeated calls for the same instance return the **same** proxy, and different instances get different proxies.

**Expected result:** `proxy` is typed as the generated interface; `counter.Aop() == counter.Aop()` is `true` by reference.

## Attach a hook set

`ProxyEx.SetProxy` takes the member kind, the member's plain name, and the three handlers:

```csharp
proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add),
    (parameters, previous) =>
    {
        Console.WriteLine($"[start] Add({parameters?[0]}, {parameters?[1]}) called");
        return null;
    },
    (parameters, previous) =>
    {
        Console.WriteLine("[coverage] original Add() body is skipped");
        return (object?)((int)(parameters?[0] ?? 0) + (int)(parameters?[1] ?? 0));
    },
    (parameters, previous) =>
    {
        Console.WriteLine($"[end] Add() returned {previous}");
        return null;
    });
```

`ProxyMembers.Getter` and `ProxyMembers.Setter` address a property's two accessors independently; `ProxyMembers.Method` addresses a method. Installing again on the same member **replaces** the whole set — there is no stacking.

## What each handler receives

| Stage | `parameters` | `previous` |
|---|---|---|
| `start` | getter: `null`; setter: `new object?[] { value }`; method: its arguments, or `null` when it has none | `null` |
| `coverage` | same as `start` | the `start` result |
| `end` | same as `start` | the member result (or the `coverage` result); `null` for a `void` member |

Only the `coverage` result is returned. `start` and `end` return values are ignored, and `end` runs after the member's own body (or after `coverage`) even for a `void` member.

**Expected result:** the triple is stored in the proxy's `AspectHooks` field for that member; no allocation or registration happens on the target.

## Read the target back

```csharp
var original = Aop.GetTarget<Counter>(proxy);
```

**Expected result:** `original` is the exact `Counter` instance; the generated factory registered it with `Aop.Map(proxy, target)`.

## Errors you can trigger

| Situation | Result |
|---|---|
| `SetProxy` on the original object instead of `Aop()`'s result | `InvalidOperationException` — aspects installed there would never run |
| Unknown member name | `ArgumentOutOfRangeException` from `IAopHookTarget.SetHooks` |
| A handler throws | the exception propagates to the proxy caller; later stages are skipped |
| `coverage` returns `null` for a value-type member | `NullReferenceException` at the generated unbox cast |
