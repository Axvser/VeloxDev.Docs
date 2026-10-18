# Data Flow — AOP

Three flows: **proxy acquisition**, **hook installation**, and **intercepted invocation**. The example uses `Demo.TeamViewModel` from `Examples/AOP/WPF/Demo`, whose generated proxy is `TeamViewModel_Demo_AopProxy`.

## 1. Proxy acquisition — `Aop()`

The generated extension is the only entry point. `AopCache` runs the factory once per target; later calls return the cached proxy.

```plantuml
@startuml
!theme plain

actor "Caller (UI)" as C
participant "Aop() extension" as E
participant "AopCache" as AC
participant "Proxy ctor" as P
participant "Aop" as AO

C -> E: team.Aop()
activate E
E -> AC: Resolve<TeamViewModel, TeamViewModel_Demo_Aop>(team, factory)
activate AC
AC -> AC: Entry<TClass,TInterface>.Instances.GetValue(team, factory)

alt cached
    AC --> E: cached TeamViewModel_Demo_AopProxy
else first call
    AC -> P: factory -> new TeamViewModel_Demo_AopProxy(team)
    activate P
    P --> AC: proxy (_target = team)
    deactivate P
    AC -> AO: Aop.Map(proxy, team)
    activate AO
    AO --> AC: (weak entry)
    deactivate AO
    AC --> E: proxy (now cached)
end

deactivate AC
E --> C: TeamViewModel_Demo_Aop
deactivate E

@enduml
```

The proxy is constructed with `new`, not through a factory API. The generated extension is:

```csharp
var p = new global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(x);
global::VeloxDev.AspectOriented.Aop.Map(p, x);
return p;
```

(emitted by `AopWriter.WriteExtension`; shown for `AopFixture`, same shape for every target.)

## 2. Hook installation — `SetProxy`

```plantuml
@startuml
!theme plain

actor "Caller" as C
participant "ProxyEx" as PX
participant "Proxy (IAopHookTarget)" as P
participant "AspectHooks" as H

C -> PX: SetProxy<T>(target, kind, name, start, coverage, end)
activate PX
alt target is not IAopHookTarget
    PX --> C: throw InvalidOperationException
else proxy
    PX -> PX: key = "get_" + name / "set_" + name / name
    PX -> H: new AspectHooks(start, coverage, end)
    activate H
    H --> PX: hooks
    deactivate H
    PX -> P: SetHooks(key, hooks)
    activate P
    alt key matches a member
        P -> P: _hooks_key = hooks
        P --> PX: (stored)
    else unknown key
        P --> PX: throw ArgumentOutOfRangeException
    end
    deactivate P
    PX --> C: void
end
deactivate PX

@enduml
```

`SetHooks` is an explicit interface implementation on the generated proxy; its `switch` has one case per interceptable accessor. Re-installing replaces the field — the previous `AspectHooks` is dropped, not composed.

## 3. Intercepted invocation

Every generated member has the same two-branch shape: **no hooks** calls the target directly; **hooks present** runs the chain.

```plantuml
@startuml
!theme plain

actor "Caller" as C
participant "TeamViewModel_Demo_AopProxy" as P
participant "AspectHooks" as H
participant "TeamViewModel (target)" as T

C -> P: p.Add(2, 3) / p.Name / p.Name = value
activate P
P -> P: h = _hooks_<key>

alt h is null (no hooks)
    P -> T: direct call (no array, no boxing, no reflection)
    T --> P: result
else hooks installed
    alt getter
        P -> H: Start?.Invoke(null, null)
    else setter
        P -> H: Start?.Invoke(new object?[]{ value }, null)
    else method with arguments
        P -> H: Start?.Invoke(new object?[]{ args... }, null)
    else parameterless method
        P -> H: Start?.Invoke(null, null)
    end
    H --> P: r0

    alt Coverage is null
        P -> T: the member's own body
        T --> P: r1
    else Coverage installed
        P -> H: Coverage.Invoke(args, r0)
        H --> P: r1
    end

    P -> H: End?.Invoke(args, r1)
    H --> P: (discarded)
end

P --> C: r1 (or the direct result)
deactivate P

@enduml
```

Applied to the demo regs in `MainWindow.xaml.cs`:

| Call | Registered stage | What happens |
|---|---|---|
| `p.Name` | getter `start` | logs the read; the body still runs and returns the value |
| `p.Name = "..."` | setter `end` | the body writes; `end` reads `args[0]` |
| `p.Reset()` | method `coverage` | the body never runs; `coverage`'s `null` result is returned |
| `p.Members.Add(...)` | `AOP_OnMemberAdded` `end` | the collection event re-enters `this.Aop()`; the method body runs, then `end` reports the new item |

### Event-driven re-entry

`TeamViewModel` subscribes to its own collection in the constructor and forwards through the proxy (`Examples/AOP/WPF/Demo/TeamViewModel.cs`):

```csharp
private void OnMemberAdded(object? sender, NotifyCollectionChangedEventArgs e)
{
    this.Aop().AOP_OnMemberAdded(sender, e);
}
```

`this.Aop()` is the same cached proxy, so the notification path is intercepted exactly like a direct call. The method body still runs (no `coverage`), and the demo's `end` hook inspects `parameters[1]` — the `NotifyCollectionChangedEventArgs`.

## 4. Error and boundary paths

| Path | Trigger | Result |
|---|---|---|
| Not a proxy | `SetProxy` on a hand-written `IAspectOriented` | `InvalidOperationException` before any state changes |
| Unknown member | `SetProxy(..., "NoSuchMember", ...)` | `ArgumentOutOfRangeException` from `SetHooks` |
| Hook throws | any non-null stage | Propagates unchanged; later stages are skipped |
| Coverage returns `null` for a value type | e.g. `int` member | `NullReferenceException` at the generated unbox |
| Coverage returns the wrong type | any member | `InvalidCastException` at the generated cast |
| Target member throws | body or direct call | Propagates unchanged — no `TargetInvocationException` wrapper |
| No hooks | any member | Direct call; no exception surface of its own |

The absence of a reflection wrapper is a behavioral improvement over the previous `MethodInfo.Invoke` design: callers catch the same exception type the target threw.

> Source: `Src/Core/VeloxDev.Core/AspectOriented/{Aop,AopCache,ProxyEx,AspectHooks}.cs`, `Src/Generators/VeloxDev.Core.Generator/{AopSurface,AopProxy}.cs`, `Writers/AopWriter.cs`, `Src/Core/VeloxDev.Core.Test/AspectOriented/AopProxyTests.cs`, `Examples/AOP/WPF/Demo/{TeamViewModel.cs,MainWindow.xaml.cs}`.
