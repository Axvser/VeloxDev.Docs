# 动态主题 — API 参考

动态主题功能提供带动画过渡的运行时主题切换。公开接口分布在核心的 `VeloxDev.DynamicTheme` 命名空间（状态、切换、存储、配置、契约）、支撑的 TransitionSystem 引擎（`VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`）以及平台适配器（`VeloxDev.WPF` / `VeloxDev.Avalonia`）中。

> 证据：示例项目 `Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo`（优先级 1）、测试 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`（优先级 2）。签名已对照 `Src/Core/VeloxDev.Core/DynamicTheme/*`、`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/*`、`Src/Core/VeloxDev.Core/TransitionSystem/*` 与 `Src/Adapters/*/PlatformAdapters/*` 验证。

## 命名空间 / 包概览

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.DynamicTheme` | `ThemeManager`、`ThemeCache`（+ 嵌套 `InstanceCache`）、`ThemeConfigAttribute<TConverter, TTheme...>`、`StartModel`、`Dark`、`Light`、`ITheme`、`IThemeObject`、`IThemeValueConverter` |
| `VeloxDev.TransitionSystem`（支撑引擎） | `InterpolatorCore`（声明于 `VeloxDev.TransitionSystem.Abstractions`）、`ITransitionEffectCore`、`IEaseCalculator`、`Eases` |
| 平台适配器（`VeloxDev.WPF` / `VeloxDev.Avalonia`） | `Interpolator`、`TransitionEffect`、`TransitionEffects`、值转换器（`DoubleConverter`、`PointConverter`、`ThicknessConverter`、`CornerRadiusConverter`、`ColorConverter`、`BrushConverter`、`ObjectConverter`） |

## 页面

| 页面 | 内容 |
|---|---|
| `00 ThemeManager` | `ThemeManager`（全部静态成员）、枚举 `StartModel`、类 `Dark` / `Light` |
| `01 ThemeCache` | `ThemeCache`（全部静态成员）、嵌套类 `InstanceCache` |
| `02 ThemeConfigAttribute` | `ThemeConfigAttribute<TConverter, TTheme...>`（6 种元数）、接口 `ITheme`、`IThemeObject`、`IThemeValueConverter` |
| `03 TransitionSystem` | 支撑引擎：`InterpolatorCore` 静态成员、`ITransitionEffectCore`、`IEaseCalculator`、`Eases` |
| `04 PlatformAdapters` | `Interpolator`、`TransitionEffect`、`TransitionEffects` 及值转换器 |

## 关键类型速览

- **`ThemeManager`** — 静态入口。`Current`、`StartModel`、`SetPlatformInterpolator<T>`、`SetCurrent<T>`、`Register` / `Unregister`、`Transition<T>` / `Transition(Type, ITransitionEffectCore)`、`Jump<T>` / `Jump(Type)`。
- **`ThemeCache`** — 主题属性值的集中存储。按类型的静态默认值加上按实例的运行时覆盖（`InstanceCache`），并带转换器注册表。
- **`ThemeConfigAttribute<TConverter, TTheme1..TTheme7>`** — 6 种元数，将一个属性映射为每个主题下的一个值。
- **`StartModel`** — `[Flags]` 枚举（`Reflect = 1`、`Cache = 2`），选择动画起始值的来源。
- **`ITheme` / `IThemeObject` / `IThemeValueConverter`** — 标记接口、生成的主题对象契约、值转换策略。
- **支撑引擎** — `InterpolatorCore.NativeInterpolators` 注册表、`ITransitionEffectCore`、`IEaseCalculator`、`Eases`。
- **平台适配器** — `Interpolator`、`TransitionEffect`（`Priority = DispatcherPriority.Render`）、`TransitionEffects`（`Empty` / `Theme` / `Hover`）及值转换器。
