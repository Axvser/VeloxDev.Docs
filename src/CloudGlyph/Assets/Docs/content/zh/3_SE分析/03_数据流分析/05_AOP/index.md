# 数据流分析 — AOP

## 1. 代理创建 + 钩子注册（`Aop()` → `SetProxy`）

```plantuml
@startuml
!theme plain

actor Caller as C
participant "生成的 Aop() 扩展" as E
participant "AopCache" as AC
participant "ProxyEx" as PX
participant "DispatchProxy" as DP
participant "ProxyInstance" as PI
participant "Aop（注册表）" as AO

C -> E: counter.Aop()
activate E
E -> AC: AopCache.Resolve(counter, factory)
activate AC
AC -> AC: 每对类型的 CWT.GetValue(counter, factory)
note right of AC: 泛型对 Counter, Counter_AopDemo_Aop
alt 已缓存代理
    AC --> E: 缓存的代理
else 首次调用
    AC -> AC: factory(counter)  （生成的 Aop() 匿名函数）
    AC -> PX: ProxyEx.CreateProxy(counter)
    activate PX
    PX -> DP: DispatchProxy.Create(proxyType, ProxyInstance)
    activate DP
    DP --> PX: 代理（Invoke 由 ProxyInstance 处理）
    deactivate DP
    PX -> PI: _target = counter; _targetType = proxyType
    PX -> PI: ProxyIDs.Add(proxy, proxy._localid)
    PX --> AC: 代理
    deactivate PX
    AC -> AO: Aop.Map(proxy, counter)  （在匿名函数内）
    AC --> E: 代理（已缓存进每对类型的 CWT）
end
deactivate AC
E --> C: 代理
deactivate E

C -> PX: proxy.SetProxy(ProxyMembers.Method, "Add", start, coverage, end)
activate PX
PX -> PI: ProxyIDs.TryGetValue(proxy, out id)
PX -> PI: ProxyInstances.TryGetValue(id, out instance)
PX -> PI: instance.MethodActions["Add"] = (start, coverage, end)
deactivate PX

@enduml
```

说明：`Aop()` 在首次调用之后，对同一目标每次都命中缓存；`SetProxy` 通过 `ProxyIDs` → `ProxyInstances` 解析出 `ProxyInstance`，当成员键已存在时会覆盖整个 `(start, coverage, end)` 三元组（`ProxyEx.cs` 第 26-41 行，`SetMethod` 第 83-101 行）。

## 2. 被拦截的调用（`proxy.Method()`）

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop 代理" as P
participant "ProxyInstance" as PI
participant "钩子处理器" as H
participant "真实目标（反射）" as T

C -> P: proxy.Add(2, 3)
activate P
P -> PI: Invoke(targetMethod = "Add", args)   （由 DispatchProxy 进入）
activate PI
PI -> PI: MethodActions.TryGetValue("Add", out actions)
alt start != null
    PI -> H: start.Invoke(args, null)
    H --> PI: R0
end
alt coverage != null
    PI -> H: coverage.Invoke(args, R0)   // 替换原逻辑
    H --> PI: R1
else coverage == null   // 反射回退
    PI -> T: _targetType.GetMethod("Add").Invoke(_target, args)
    T --> PI: R1
end
alt end != null
    PI -> H: end.Invoke(args, R1)
    H --> PI: null
end
PI --> P: 返回 R1
deactivate PI
P --> C: 结果
deactivate P

@enduml
```

属性访问器形状相同：名字以 `get_` 开头的路由到 `GetterActions`，`set_*` 路由到 `SetterActions`，其余路由到 `MethodActions`（`ProxyInstance.cs` 第 23-53 行）。钩子顺序始终是 `start` →（`coverage`，或反射）→ `end`。

## 3. 错误路径

### 3a. 钩子抛出异常 → 传播

`ProxyInstance.Invoke` 内部没有 try/catch，因此任何处理器抛出的异常都会直接传播给调用方，并跳过其余阶段与任何反射调用：

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop 代理" as P
participant "ProxyInstance" as PI
participant "start 处理器" as H

C -> P: proxy.Reset()
activate P
P -> PI: Invoke(targetMethod = "Reset", args)
activate PI
PI -> H: start.Invoke(args, null)
activate H
H --> PI: throw InvalidOperationException
deactivate H
note over PI: Invoke 内部没有 try/catch<br/>coverage / end / 反射全部跳过
PI --> P: 异常传播
deactivate PI
P --> C: 异常到达调用方
deactivate P

@enduml
```

### 3b. `coverage == null` 的反射回退

当 `coverage` 为 `null` 时，代理对真实目标做反射。若接口类型上解析不到该成员，`GetMethod` 返回 `null`，`?.` 短路，于是调用在不执行原方法体的情况下静默返回 `null`：

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_Ns_Aop 代理" as P
participant "ProxyInstance" as PI
participant "真实目标" as T
participant "end 处理器" as H

C -> P: proxy.SomeMember()
activate P
P -> PI: Invoke(targetMethod = name, args)
activate PI
PI -> PI: MethodActions.TryGetValue(name, out actions)   // coverage = null
PI -> T: _targetType.GetMethod(name)
T --> PI: null   // 生成的接口类型上找不到该成员
note over PI: R1 = null（?. 短路）—— 原方法体不执行
PI -> H: end.Invoke(args, null)
H --> PI: null
PI --> P: 返回 null
deactivate PI
P --> C: null
deactivate P

@enduml
```

若 `GetMethod` 找到了成员但反射 `Invoke` 抛异常（例如目标抛错或实参不匹配），该异常会被 `MethodInfo.Invoke` 包装成 `TargetInvocationException` 并传播给调用方；任何 `end` 钩子都会被跳过。

## 流程汇总

| 路径 | 触发条件 | 结果 |
|---|---|---|
| 创建代理 | 首次调用 `instance.Aop()` | 创建 `DispatchProxy`，设置 `_target`/`_targetType`，登记到 `ProxyIDs`，经 `Aop.Map` 映射，缓存进每对类型的 CWT |
| 注册钩子 | `proxy.SetProxy(memberType, name, s, c, e)` | 把 `(s, c, e)` 写入 `GetterActions` / `SetterActions` / `MethodActions` |
| 正常调用 | `proxy.Member(...)` | `start` → `coverage`（或反射回退）→ `end` → 返回 `R1` |
| 钩子抛异常 | 任意非空钩子 | 异常传播给调用方；其余阶段跳过 |
| 反射回退 | `coverage == null` | `_targetType.GetMethod(Name)?.Invoke(_target, args)`；找不到则返回 `null` |
| 反射抛异常 | `coverage == null` 且找到成员 | `TargetInvocationException` 传播给调用方；`end` 跳过 |

> 出处汇总：`Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`、`ProxyEx.cs`、`AopCache.cs`、`Aop.cs`、`Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs`。
