# 数据流 — 动态主题

## 注册流程（`InitializeTheme`）

源生成器生成的 `InitializeTheme()` 会在 `ThemeCache` 中注册该类型的主题属性、向 `ThemeManager` 注册实例，并应用当前主题的值。

```plantuml
@startuml
!theme plain

actor User as User
participant "MainWindow\n(generated IThemeObject)" as TO
participant "ThemeCache" as TC
participant "ThemeManager" as TM

User -> TO: InitializeTheme()
activate TO

TO -> TC: RegisterType(typeof(MainWindow), properties)
activate TC
TC --> TO: cached (duplicate ignored)
deactivate TC

TO -> TM: Register(this)
activate TM
TM -> TM: _act_cache.Add(this, [])\nactiveThemes.Add(new WeakReference(this))
TM --> TO: registered
deactivate TM

TO -> TO: apply current theme values (Current = Dark)
TO --> User: ready
deactivate TO
@enduml
```

> 源码：`VeloxDev.Generators.Theme` 生成的代码形态；注册支撑代码见 `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（`Register`）与 `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`（`RegisterType`）。

## 带动画主题切换（`Transition<T>`）

`ThemeManager.Transition` 校验目标主题、取消正在运行的过渡、清理失效的 `WeakReference`，准备每属性采样器，然后在效果的时长内以 Stopwatch 驱动循环采样。

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "ThemeCache" as TC
participant "InterpolatorCore" as IK
participant "IThemeObject" as TO
participant "PropertyInfo" as PI

User -> TM: Transition<Light>(TransitionEffects.Theme)
activate TM

note right of TM
  durationMs = effect.Duration.TotalMilliseconds
  sampling loop: rawT = stopwatch.Elapsed / durationMs
end note

TM -> TM: CancleTransition()
TM -> TM: prune dead WeakReferences

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanging)
deactivate TO

loop each registered object, each themed property
    TM -> IK: TryGetInterpolator(propertyType, out sampleable)
    activate IK
    IK --> TM: ISampleable? or null
    deactivate IK

    alt sampleable found (registered native / self-ISampleable)
        TM -> TC: TryGetDefaultValue(type, prop, Dark, out start)\nor active cache value
        activate TC
        TC --> TM: start value (Cache) / live value (Reflect)
        deactivate TC
    else no sampleable
        note right of TM
          simple switch: hold current value, jump to target at the end
        end note
    end
    TM -> TM: sampler = sampleable.Normalize(current, targetValue, null)
    TM -> TM: TransitionEntry(target, property, sampler, current, targetValue)
end

TM -> TM: stopwatch = Stopwatch.StartNew()

loop until rawT >= 1 (Stopwatch-driven, 1ms coarse yield)
    TM -> TM: rawT = elapsed / durationMs  (clamped to [0,1])
    TM -> TM: easedT = clamp(Ease(rawT), 0, 1)
    loop each TransitionEntry
        alt rawT >= 1 (end)
            TM -> PI: SetValue(target, targetValue)
        else sampler == null
            note right of TM
              hold current value (no write)
            end note
        else
            TM -> TM: sampler.Update(target, property, current, targetValue, null, applyT)\n(writes via TransitionProperty)
        end
        activate PI
        PI --> TM: property updated
        deactivate PI
    end
end

TM -> TM: Current = typeof(Light)
TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

> 源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Transition`、`PrepareSamplers`、`ExecuteTransition`。采样器解析经由 `InterpolatorCore.TryGetInterpolator` 得 `ISampleable`，经 `Normalize` 得 `ISampler`；每次采样的值经 `ISampler.Update` 写入。

## 即时主题切换（`Jump<T>`）

`Jump` 复用同一采样器管线，但时长为零（`durationMs = 0`），因此首次采样即 `rawT = 1`，每个属性都直接设置为目标值。

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "IThemeObject" as TO

User -> TM: Jump<Light>()
activate TM

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanging)
deactivate TO

TM -> TM: PrepareSamplers(actives, themeType)
TM -> TM: ExecuteTransition(entries, Eases.Default, 0d, themeType)\n(rawT = 1 immediately → each property set directly to target value)
TM -> TM: Current = typeof(Light)

TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

> 源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Jump(Type)`。

## 异常 / 边界路径

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM

== Invalid theme type (not an ITheme) ==
User -> TM: Transition(typeof(object), effect)
activate TM
TM -> TM: typeof(ITheme).IsAssignableFrom(typeof(object)) == false
TM -> TM: Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")
TM --> User: return (no-op)
deactivate TM

== themeType == Current ==
User -> TM: Transition<Dark>(effect)
activate TM
TM -> TM: themeType == Current  → aborted early
TM -> TM: Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")
TM --> User: return (no-op)
deactivate TM

== Zero-duration effect ==
User -> TM: Transition<Light>(TransitionEffects.Empty)
activate TM
note right of TM
  durationMs = 0 → rawT = 1 on the first sample
end note
TM -> TM: apply final values (end-value writes), Current = typeof(Light)
TM --> User: return
deactivate TM
@enduml
```

## 正常路径与边界路径汇总

| 场景 | 行为 |
|---|---|
| 正常动画切换 | 准备每属性 `ISampleable` 并 `Normalize` 得到 `ISampler`，然后在 `Duration` 内对每个已注册对象的主题属性调用 `sampler.Update(...)`（Stopwatch 驱动、缓动 + 钳制），随后设置 `Current` 并触发 `OnThemeChanged`。 |
| `themeType == Current` | 提前终止 — 调试信息「Invalid theme type, jumping to current theme.」 |
| `themeType` 不实现 `ITheme` | 同样提前终止并输出该调试信息。 |
| 属性无采样器 | 退化为简单的切换（整趟持有 `current` 值，最后一次采样写入 `target`）；`Jump`/`SetThemeValue` 仍会设置最终值。 |
| 目标主题对该属性没有配置值 | `PrepareSamplers` 记录「No target value found」并在过渡中跳过该属性。 |
| 零时长效果（`durationMs = 0`） | 首次采样即 `rawT = 1`，每个属性直接写入目标值；主题仍会应用。 |

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（`Transition`、`Jump`、`PrepareSamplers`、`ExecuteTransition`）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`。
