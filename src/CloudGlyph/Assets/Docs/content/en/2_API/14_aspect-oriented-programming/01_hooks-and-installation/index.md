# Hooks and Installation

The three-stage hook model and the installer reached from a proxy. Namespace `VeloxDev.AspectOriented`.

## VeloxDev.AspectOriented

### Delegate: ProxyHandler

One stage of an aspect.

**Signature:** `public delegate object? ProxyHandler(object?[]? parameters, object? previous)`

| Parameter | Type | Description |
|---|---|---|
| `parameters` | `object?[]?` | A getter receives `null`; a setter receives one element, the value being written; a method receives its own arguments. |
| `previous` | `object?` | What the preceding stage returned; `null` for `start`. |

**Returns:** for `start`, the value handed to the next stage as `previous`; for `coverage`, the member's result; for `end`, discarded.

### Class: AspectHooks

The three stages installed together on one member.

**Signature:** `public sealed class AspectHooks(ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end)`

| Member | Type | Description |
|---|---|---|
| `Start` | `ProxyHandler?` | Runs before the member; its return value becomes the next stage's `previous`. |
| `Coverage` | `ProxyHandler?` | When non-null, replaces the member: the body does not run and this return value is the member's result. |
| `End` | `ProxyHandler?` | Runs after the member; its return value is discarded. |

A hook set is installed whole. There is no way to keep one stage and replace another; passing `null` for the set clears the member's aspects.

### Interface: IAopHookTarget

The installation surface every generated proxy implements. Normally called through `ProxyEx.SetProxy`, not by hand.

**Signature:** `public interface IAopHookTarget`

| Member | Signature | Description |
|---|---|---|
| `SetHooks` | `void SetHooks(string memberKey, AspectHooks? hooks)` | Installs or clears one member's aspects. The key is `get_Name`, `set_Name`, or a method's own name. |

**Exceptions:** `ArgumentOutOfRangeException` when `memberKey` is not a member of the proxied type.

### Enum: ProxyMembers

Which accessor an aspect is installed on.

**Signature:** `public enum ProxyMembers`

| Member | Meaning |
|---|---|
| `Getter` | The property's getter. |
| `Setter` | The property's setter. |
| `Method` | A method. |

A property's getter and setter are separate members and take separate aspects.

### Class: ProxyEx

Installs aspects on the proxy a generated `Aop()` returns.

**Signature:** `public static class ProxyEx`

| Member | Signature | Description |
|---|---|---|
| `SetProxy<T>` | `static void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : IAspectOriented` | Installs the three stages on one member. `memberType` selects `get_` / `set_` / bare name. |

**Exceptions**

| Exception | Condition |
|---|---|
| `InvalidOperationException` | `target` is the original object rather than a proxy. Installing there would never run, so it is refused rather than ignored. |
| `ArgumentOutOfRangeException` | `memberName` is not an interceptable member of the proxied type. |

Installing on the same member twice **replaces** all three stages.

## Example

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();

// Before a read.
proxy.SetProxy(ProxyMembers.Getter, nameof(CounterViewModel.Value),
    (parameters, previous) => { Console.WriteLine("[getter before]"); return null; },
    null,
    null);

// After a write.
proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) =>
    {
        Console.WriteLine($"[setter after] {parameters?[0]}");
        return null;
    });

// Replace a method body.
proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);

Console.WriteLine($"read: {proxy.Value}");
proxy.Value = 7;
proxy.Reset();
```

## Notes

- `start` can short-circuit `coverage`'s shared state by returning a prepared object; `coverage` receives it as `previous`. A `coverage` handler that ignores `previous` still replaces the body.
- For a `void` method, `coverage`'s return value is ignored.
- The handlers are boxed by design. That is what keeps the generated proxies free of reflection and runtime code generation.
- An aspect installed on `counter` (the original object) is refused; the check runs before any key resolution.
