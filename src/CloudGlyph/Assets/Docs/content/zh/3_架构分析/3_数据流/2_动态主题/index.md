# 数据流 — 动态主题

## 带动画主题切换（`Transition<T>`）

核心 API 调用链。`ThemeManager.Transition` 预先计算所有插值帧，然后按帧定时应用到对象上。

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
  steps = Duration / (1000 / FPS)
  deltaTime = Duration / steps
end note

TM -> TM: CancleTransition()
TM -> TM: 清理失效的 WeakReference

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (触发 OnThemeChanging)
deactivate TO

TM -> IK: TryGetInterpolator(propertyType, out interp)
activate IK
IK --> TM: interp 或 null
deactivate IK

alt 找到插值器
    TM -> TC: TryGetDefaultValue(type, prop, Dark, out start)
    activate TC
    TC --> TM: 起始值（Cache）或当前属性值（Reflect）
    deactivate TC
    TM -> IK: Interpolate(start, end, steps, options)
    activate IK
    IK --> TM: List<object?> 帧（经 EaseCalculator 缓动）
    deactivate IK
else 无插值器
    note right of TM
      该属性在动画中被跳过
    end note
end

loop 每帧（间隔 deltaTime）
    TM -> PI: SetValue(target, frame[i])
    activate PI
    PI --> TM: 属性已更新
    deactivate PI
end

TM -> TM: Current = typeof(Light)
TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (触发 OnThemeChanged)
deactivate TO

TM --> User: 返回
deactivate TM
@enduml
```

## 即时切换（`Jump<T>`）

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
TO --> TM: (触发 OnThemeChanging)
deactivate TO

TM -> TM: 直接设置每个属性为新主题值（无插值）
TM -> TM: Current = typeof(Light)

TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (触发 OnThemeChanged)
deactivate TO

TM --> User: 返回
deactivate TM
@enduml
```

## 运行时值覆盖（`SetThemeValue<T>`）

```plantuml
@startuml
!theme plain

actor User as User
participant "IThemeObject (生成)" as TO
participant "ThemeCache" as TC

User -> TO: SetThemeValue<Light>(nameof(Background), new value)
activate TO

TO -> TC: GetOrCreateActiveEntry(this)
activate TC
TC --> TO: InstanceCache (overrides)
deactivate TC

TO -> TC: 查找属性的转换器
TO -> TO: 将原始值转换为平台类型

TO -> TO: UpdatePropertyToCurrentTheme(Background)
TO --> User: 属性立即更新
deactivate TO
@enduml
```

## 正常路径与异常路径

| 场景 | 行为 |
|---|---|
| 正常动画切换 | 在 `Duration` 内对每个已注册对象的属性插值，然后设置 `Current` 并触发 `OnThemeChanged`。 |
| `themeType == Current` | 提前终止 — 调试信息「Invalid theme type, jumping to current theme.」 |
| `themeType` 不实现 `ITheme` | 同样提前终止。 |
| 属性无插值器 | 动画中跳过该属性；仍由 `Jump`/`SetThemeValue` 设置为最终值。 |
| `steps <= 0`（零时长效果） | 钳制为 `steps = 1`，主题仍会应用。 |

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（第 83–106 行 `Transition`、153–407 行 `CalculateFrames`、414–452 行 `ExecuteTransition`）、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。
