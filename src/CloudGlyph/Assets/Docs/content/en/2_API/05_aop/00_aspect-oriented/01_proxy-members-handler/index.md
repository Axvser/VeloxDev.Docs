# AOP runtime — hook contracts

Four types define what can be hooked and what a hook looks like: `ProxyMembers` selects the accessor, `ProxyHandler` is the delegate signature, `AspectHooks` bundles the three stages, and `IAopHookTarget` is the installation surface implemented by the generated proxy.

All four live in `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs` (the enum and `ProxyEx`) and `AspectHooks.cs` (the delegate, `AspectHooks`, `IAopHookTarget`).

## Type: `ProxyMembers` (enum)

```csharp
public enum ProxyMembers
{
    Getter,
    Setter,
    Method
}
```

Selects the interception key `ProxyEx.SetProxy` builds:

| Member | Key written | Example |
|---|---|---|
| `Getter` | `"get_" + memberName` | `get_Name` |
| `Setter` | `"set_" + memberName` | `set_Name` |
| `Method` | `memberName` verbatim | `Reset` |

A property's getter and setter are separate members with separate hook sets.

## Type: `ProxyHandler` (delegate)

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

| Parameter | Type | Description |
|---|---|---|
| `parameters` | `object?[]?` | Getter: `null`. Setter: one element, the value written. Method: the arguments, or `null` when the method has none. |
| `previous` | `object?` | `null` for `start`; the `start` result for `coverage`; the produced result for `end`. |

**Returns:** `object?` — honored only for `coverage`, where it becomes the member's result.

**Exceptions:** none declared. A handler may throw; the exception propagates to the proxy caller and the remaining stages do not run.

## Type: `AspectHooks` (sealed class)

```csharp
public sealed class AspectHooks(ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end)
{
    public ProxyHandler? Start { get; }
    public ProxyHandler? Coverage { get; }
    public ProxyHandler? End { get; }
}
```

One set per member. A set is installed whole: you cannot replace one stage while keeping another. `null` for the whole set clears that member's aspects (the generated `SetHooks` assigns the slot).

## Type: `IAopHookTarget` (interface)

```csharp
public interface IAopHookTarget
{
    void SetHooks(string memberKey, AspectHooks? hooks);
}
```

Implemented explicitly by every generated proxy. User code reaches it only through `ProxyEx.SetProxy`.

**Exceptions:**

| Exception | Condition |
|---|---|
| `System.ArgumentOutOfRangeException` | `memberKey` matches no interceptable member of the proxied type |

An unknown key throws rather than doing nothing: a silently ignored aspect is the failure mode this API is designed to prevent.

## Stage order

For a member with hooks, the generated proxy runs:

```text
R0 = Start?.Invoke(parameters, null)
R1 = Coverage is null ? <the member's own body> : Coverage.Invoke(parameters, R0)
End?.Invoke(parameters, R1)
return R1
```

`Start` sees no result; `Coverage` replaces the body when non-null; `End` observes the final result and its own return value is discarded. A `void` member has `R1 == null`.

Related pages: [ProxyEx](../02_proxyex/index.md) installs these sets; [Generated proxy](../03_proxy-class/index.md) runs them.
