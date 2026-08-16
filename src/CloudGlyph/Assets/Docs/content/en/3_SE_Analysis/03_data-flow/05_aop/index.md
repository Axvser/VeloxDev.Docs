# Data Flow — AOP

## 1. Proxy creation + hook registration (`Aop()` → `SetProxy`)

```plantuml
@startuml
!theme plain

actor Caller as C
participant "Generated Aop() ext" as E
participant "AopCache" as AC
participant "ProxyEx" as PX
participant "DispatchProxy" as DP
participant "ProxyInstance" as PI
participant "Aop (registry)" as AO

C -> E: counter.Aop()
activate E
E -> AC: AopCache.Resolve(counter, factory)
activate AC
AC -> AC: per-pair CWT.GetValue(counter, factory)
note right of AC: generic pair Counter, Counter_AopDemo_Aop
alt proxy already cached
    AC --> E: cached proxy
else first call
    AC -> AC: factory(counter)  (generated Aop() lambda)
    AC -> PX: ProxyEx.CreateProxy(counter)
    activate PX
    PX -> DP: DispatchProxy.Create(proxyType, ProxyInstance)
    activate DP
    DP --> PX: proxy (Invoke handled by ProxyInstance)
    deactivate DP
    PX -> PI: _target = counter; _targetType = proxyType
    PX -> PI: ProxyIDs.Add(proxy, proxy._localid)
    PX --> AC: proxy
    deactivate PX
    AC -> AO: Aop.Map(proxy, counter)  (inside lambda)
    AC --> E: proxy (now cached in the per-pair CWT)
end
deactivate AC
E --> C: proxy
deactivate E

C -> PX: proxy.SetProxy(ProxyMembers.Method, "Add", start, coverage, end)
activate PX
PX -> PI: ProxyIDs.TryGetValue(proxy, out id)
PX -> PI: ProxyInstances.TryGetValue(id, out instance)
PX -> PI: instance.MethodActions["Add"] = (start, coverage, end)
deactivate PX

@enduml
```

Notes: `Aop()` is a one-time-per-target cache hit after the first call; `SetProxy` resolves the `ProxyInstance` through `ProxyIDs` → `ProxyInstances` and overwrites the whole `(start, coverage, end)` triple when the member key already exists (`ProxyEx.cs` lines 26-41, `SetMethod` lines 83-101).

## 2. Intercepted invocation (`proxy.Method()`)

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop proxy" as P
participant "ProxyInstance" as PI
participant "Hook handlers" as H
participant "Real target (reflection)" as T

C -> P: proxy.Add(2, 3)
activate P
P -> PI: Invoke(targetMethod = "Add", args)   (entered by DispatchProxy)
activate PI
PI -> PI: MethodActions.TryGetValue("Add", out actions)
alt start != null
    PI -> H: start.Invoke(args, null)
    H --> PI: R0
end
alt coverage != null
    PI -> H: coverage.Invoke(args, R0)   // replaces original logic
    H --> PI: R1
else coverage == null   // reflection fallback
    PI -> T: _targetType.GetMethod("Add").Invoke(_target, args)
    T --> PI: R1
end
alt end != null
    PI -> H: end.Invoke(args, R1)
    H --> PI: null
end
PI --> P: return R1
deactivate PI
P --> C: result
deactivate P

@enduml
```

The same shape applies to property accessors: a name starting with `get_` routes to `GetterActions`, `set_*` to `SetterActions`, everything else to `MethodActions` (`ProxyInstance.cs` lines 23-53). The hook order is always `start` → (`coverage`, or reflection) → `end`.

## 3. Error paths

### 3a. A hook throws → propagation

`ProxyInstance.Invoke` contains no try/catch, so any handler exception flows straight out to the caller, skipping the remaining stages and any reflection call:

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop proxy" as P
participant "ProxyInstance" as PI
participant "Start handler" as H

C -> P: proxy.Reset()
activate P
P -> PI: Invoke(targetMethod = "Reset", args)
activate PI
PI -> H: start.Invoke(args, null)
activate H
H --> PI: throw InvalidOperationException
deactivate H
note over PI: no try/catch inside Invoke<br/>coverage / end / reflection all skipped
PI --> P: exception propagates
deactivate PI
P --> C: exception reaches caller
deactivate P

@enduml
```

### 3b. `coverage == null` reflection fallback

With a `null` coverage, the proxy reflects into the real target. If the member cannot be resolved on the interface type, `GetMethod` returns `null` and the `?.` short-circuits, so the call silently returns `null` without executing the original body:

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop proxy" as P
participant "ProxyInstance" as PI
participant "Real target" as T
participant "End handler" as H

C -> P: proxy.SomeMember()
activate P
P -> PI: Invoke(targetMethod = name, args)
activate PI
PI -> PI: MethodActions.TryGetValue(name, out actions)   // coverage = null
PI -> T: _targetType.GetMethod(name)
T --> PI: null   // member not found on the generated interface type
note over PI: R1 = null  (?.) — original body is NOT executed
PI -> H: end.Invoke(args, null)
H --> PI: null
PI --> P: return null
deactivate PI
P --> C: null
deactivate P

@enduml
```

If `GetMethod` does find the member but the reflection `Invoke` throws (e.g. the target throws, or argument mismatch), the exception is wrapped by `MethodInfo.Invoke` as a `TargetInvocationException` and propagates to the caller; any `end` hook is skipped.

## Flow summary

| Path | Trigger | Result |
|---|---|---|
| Proxy creation | `instance.Aop()` first call | `DispatchProxy` created, `_target`/`_targetType` set, registered in `ProxyIDs`, mapped via `Aop.Map`, cached in per-pair CWT |
| Hook registration | `proxy.SetProxy(memberType, name, s, c, e)` | `(s, c, e)` written into `GetterActions` / `SetterActions` / `MethodActions` |
| Normal call | `proxy.Member(...)` | `start` → `coverage` (or reflection fallback) → `end` → return `R1` |
| Hook throws | any non-null hook | Exception propagates to caller; remaining stages skipped |
| Reflection fallback | `coverage == null` | `_targetType.GetMethod(Name)?.Invoke(_target, args)`; `null` if not found |
| Reflection throws | `coverage == null`, member found | `TargetInvocationException` propagates to caller; `end` skipped |

> Source references: `Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`, `ProxyEx.cs`, `AopCache.cs`, `Aop.cs`, `Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs`.
