# AOP runtime — generated proxy class

The class that actually intercepts is not a library type: `AopSurface` emits it into the consumer's assembly. Its shape is fixed by `AopSurface.WriteProxy` (`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`), and the emitted output can be inspected under the test project's `obj/.../generated/` directory after a build.

## Shape

For `AopFixture` (`Src/Core/VeloxDev.Core.Test/AspectOriented/AopFixture.cs`), the generated file `AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy.g.cs` begins:

```csharp
namespace VeloxDev.AopInterfaces;

internal sealed class AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy : AopFixture_VeloxDev_Core_Test_AspectOriented_Aop
{
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Add;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Ping;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Echo;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_get_Title;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_set_Title;

    private readonly global::VeloxDev.Core.Test.AspectOriented.AopFixture _target;

    internal AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(global::VeloxDev.Core.Test.AspectOriented.AopFixture target) => _target = target;
```

One `AspectHooks?` field exists per interceptable accessor, keyed by the same name `SetProxy` builds. The constructor is `internal`; only the generated `Aop()` extension constructs it.

## Fast path — no hooks

Every member starts with a null check:

```csharp
public int Add(int a, int b)
{
    var h = _hooks_Add;
    if (h is null)
    {
        return _target.Add(a, b);

    }
    // ...
}
```

With no hook set, the member calls the target directly. No array is allocated, no boxing occurs, and no reflection is involved. This is what a member that was never registered costs.

## Hook path

**Method with a return value:**

```csharp
var args = new object?[] { a, b };
var r0 = h.Start?.Invoke(args, null);
object? r1;
if (h.Coverage is null)
{
    r1 = _target.Add(a, b);
}
else
{
    r1 = h.Coverage.Invoke(args, r0);
}

h.End?.Invoke(args, r1);
return (int)r1!;
```

**Method without parameters** passes `object?[]? args = null;` instead of allocating an empty array.

**Void method** executes the same stages, sets `r1 = null` when `Coverage` is null, calls `End`, and returns nothing. A void member's `end` therefore always receives `null`.

**Property getter** passes `null` as the parameter array:

```csharp
var r0 = h.Start?.Invoke(null, null);
var r1 = h.Coverage is null
    ? (object?)_target.Title
    : h.Coverage.Invoke(null, r0);
h.End?.Invoke(null, r1);
return (string)r1!;
```

**Property setter** passes `new object?[] { value }`; when `Coverage` is null it writes `_target.Property = value` before running `end`, and it returns nothing.

## `SetHooks` dispatch

```csharp
void global::VeloxDev.AspectOriented.IAopHookTarget.SetHooks(string memberKey, global::VeloxDev.AspectOriented.AspectHooks? hooks)
{
    switch (memberKey)
    {
        case "Add": _hooks_Add = hooks; return;
        case "Ping": _hooks_Ping = hooks; return;
        case "Echo": _hooks_Echo = hooks; return;
        case "get_Title": _hooks_get_Title = hooks; return;
        case "set_Title": _hooks_set_Title = hooks; return;
        default:
            throw new global::System.ArgumentOutOfRangeException(nameof(memberKey), memberKey, "not an interceptable member of VeloxDev.Core.Test.AspectOriented.AopFixture");
    }
}
```

The method is an explicit interface implementation, so it is not part of the proxy's public surface.

## Exceptions

| Situation | Result |
|---|---|
| Hook throws in `Start` / `Coverage` / `End` | Propagates unchanged; later stages are skipped |
| `Coverage` returns `null` for a value-type member | `NullReferenceException` at the generated unbox `(T)r1!` |
| `Coverage` returns the wrong type | `InvalidCastException` at the same cast |
| Target member throws | Propagates unchanged — **not** wrapped in `TargetInvocationException`, unlike the old reflection-based design |

## Threading

The proxy has no locks. `AspectHooks` is immutable, and a hook field is read once per call (`var h = _hooks_Add;`), so a concurrent `SetProxy` affects subsequent calls rather than the one in flight. Hook delegates themselves must be thread-safe if the intercepted member can be called concurrently.
