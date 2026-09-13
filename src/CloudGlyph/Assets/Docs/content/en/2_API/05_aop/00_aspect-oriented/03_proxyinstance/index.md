# AOP runtime — `ProxyInstance`

`Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`. The single interception point shared by every generated proxy. `ProxyEx.CreateProxy` (see [proxyex](../02_proxyex/index.md)) creates it through `DispatchProxy.Create<T, ProxyInstance>()`, then fills in its internal state.

## Class shape

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    public ProxyInstance() { _localid = Guid.NewGuid(); ProxyInstances.Add(_localid, this); }

    internal object? _target = null;
    internal Type? _targetType = null;
    internal Guid _localid = Guid.Empty;

    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> GetterActions { get; set; } = [];
    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> SetterActions { get; set; } = [];
    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> MethodActions { get; set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args) { /* dispatch, below */ }
}
```

The three hook tables (`GetterActions`, `SetterActions`, `MethodActions`) are `internal`; they map the dispatched member-name key to the `(start, coverage, end)` triple that `ProxyEx.SetProxy` writes. The `_target` / `_targetType` fields hold the wrapped instance and its proxy-interface type respectively.

## ProxyInstance.ProxyInstances

**Signature:** `static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; }`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Static property — global registry mapping each proxy's local `Guid` to its `ProxyInstance` |

**Returns:** `Dictionary<Guid, ProxyInstance>`

**Notes:** populated by the `ProxyInstance` constructor (each proxy gets a fresh `Guid`). `ProxyEx.SetProxy` resolves the instance through `ProxyIDs[target]` then this table to reach the hook tables.

## ProxyInstance.ProxyIDs

**Signature:** `static Dictionary<object, Guid> ProxyIDs { get; internal set; }`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Static property — maps a proxy object to its local `Guid` |

**Returns:** `Dictionary<object, Guid>`

**Notes:** populated by `ProxyEx.CreateProxy`. `SetProxy` uses it to look up the owning `ProxyInstance` from the proxy passed as `target`.

## Constructor: `ProxyInstance`

**Signature:** `ProxyInstance()`

**Returns:** `ProxyInstance`

**Notes:** public parameterless constructor. Generates `_localid = Guid.NewGuid()` and registers `_localid → this` in `ProxyInstances`. It is invoked by `DispatchProxy.Create<T, ProxyInstance>()`, not called directly in user code.

## ProxyInstance.Invoke

**Signature:** `protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)` — invoked by `DispatchProxy` on every proxied interface-member call.

| Parameter | Type | Description |
|---|---|---|
| `targetMethod` | `MethodInfo?` | The interface member being called (`targetMethod.Name` carries the `get_` / `set_` / method name) |
| `args` | `object?[]?` | The call arguments, boxed |

**Returns:** `object?` — the `coverage` handler's result, or the reflected real-member result (`R1`).

### Dispatch rules (source-verified)

```csharp
protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
{
    var Name = targetMethod?.Name ?? string.Empty;

    if (Name == string.Empty) return null;

    if (Name.StartsWith("get_"))
    {
        GetterActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
    else if (Name.StartsWith("set_"))
    {
        SetterActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
    else
    {
        MethodActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
}
```

Behavior:

- `Name` empty / `null` → return `null`.
- Name starting with `get_` looks up `GetterActions`, then `set_` → `SetterActions`, otherwise → `MethodActions`. The stored `Tuple` is unpacked as `Item1 = start`, `Item2 = coverage`, `Item3 = end`.
- With no registered triple (`TryGetValue` fails) `actions` is `null`, so the member is still forwarded to the real instance: `_targetType.GetMethod(Name).Invoke(_target, args)`.
- When a `coverage` hook is registered it replaces the body entirely and its return value becomes the member's result (`R1`); a non-null `start` result only feeds `coverage` as `previous`, and the `end` return value is discarded.

**Exceptions:** a hook or the reflection call may throw; the exception propagates to the proxy caller — there is no `try/catch` inside `Invoke`.

Related pages: [ProxyEx](../02_proxyex/index.md) creates and configures this type; [Aop & AopCache](../04_proxy-lifecycle/index.md) covers lifecycle helpers.
