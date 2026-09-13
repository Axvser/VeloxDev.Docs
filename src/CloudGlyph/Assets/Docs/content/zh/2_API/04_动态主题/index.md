# 动态主题 — API 参考

动态主题功能在运行时于主题类型（`Dark` / `Light` / 自定义）之间切换，并通过 TransitionSystem 采样引擎对每个主题属性做动画。公开接口分布在核心的 `VeloxDev.DynamicTheme` 命名空间、主题源生成器、支撑的过渡引擎以及各平台适配器中。

> 证据：示例项目 `Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo`（优先级 1）、测试 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` 与 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeTransitionTests.cs`（优先级 2）。签名已对照 `Src/Core/VeloxDev.Core/DynamicTheme/**`、`Src/Core/VeloxDev.Core/TransitionSystem/**`、`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/**`、主题生成器 `Src/Generators/VeloxDev.Core.Generator/Theme.cs` 以及 `Src/Adapters/**` 下的适配器主题文件验证。

## 公开接口分布

| 区域 | 命名空间 / 位置 | 内容 |
|---|---|---|
| 核心契约 | `VeloxDev.DynamicTheme`（在 `VeloxDev.Core` 中） | `ThemeManager`、`ThemeCache`（+ 嵌套 `InstanceCache`）、`ThemeConfigAttribute<TConverter, TTheme...>`、枚举 `StartModel`、`Dark`、`Light`、`ITheme`、`IThemeObject`、`IThemeValueConverter` |
| 源生成器 | `VeloxDev.Generators.Theme` | 为携带 `[ThemeConfig<...>]` 的类生成 `IThemeObject` 的 partial 实现 |
| 支撑引擎 | `VeloxDev.TransitionSystem` / `.Abstractions` | `InterpolatorCore`、`TransitionSchedulerCore`、`TransitionTimeline`、`TransitionCore`、`ISampler`、`ISampleable`、`ITransitionProperty` / `TransitionProperty`、`ITransitionEffectCore`、`IEaseCalculator`、`Eases` |
| 平台适配器 | `VeloxDev.WPF` / `VeloxDev.Avalonia`（以及 `MAUI` / `WinUI` / `WinForms` / `Razor`） | 适配器 `Interpolator`、`TransitionEffect` / `TransitionEffects`、主题值转换器（`DoubleConverter`、`PointConverter`、`ThicknessConverter`、`CornerRadiusConverter`、`ColorConverter`、`BrushConverter`、`ObjectConverter`） |

## 关键类型速览

- **`ThemeManager`** — 静态入口。`Current`、`StartModel`、`SetPlatformInterpolator<T>`、`SetCurrent<T>`、`Register` / `Unregister`、`Transition<T>` / `Transition(Type, ITransitionEffectCore)`（`async void`，在过渡系统上运行）、`Jump<T>` / `Jump(Type)`（同步，直接写终值、无动画）。
- **`ThemeCache`** — 主题属性值的集中存储：按类型的静态默认值，加上按实例的运行时覆盖（`InstanceCache`），并带共享转换器注册表。
- **`ThemeConfigAttribute<TConverter, TTheme1..TThemeN>`** — 六种元数（2 到 7 个主题类型），把一个属性映射为每个主题下的一个值。
- **`StartModel`** — `[Flags]` 枚举（`Reflect = 1`、`Cache = 2`），选择动画起始值的来源。
- **`ITheme` / `IThemeObject` / `IThemeValueConverter`** — 主题标记、生成的主题对象契约、值转换策略。
- **支撑引擎** — 静态采样器注册表 `InterpolatorCore.NativeInterpolators`（`ConcurrentDictionary<Type, ISampler>`）、平台接缝 `InterpolatorCore.CreateScheduler` / `TransitionSchedulerCore` / 共享 `TransitionTimeline`、采样契约 `ISampler`/`ISampleable`、属性契约 `TransitionProperty`，以及效果/缓动契约 `ITransitionEffectCore` / `IEaseCalculator` / `Eases`。
- **平台适配器** — 适配器 `Interpolator`、效果预设 `TransitionEffects`（`Empty` / `Theme` / `Hover`）与主题值转换器。

## 页面

- [00 ThemeManager](00_ThemeManager/index.md) — `ThemeManager`（全部静态成员）、枚举 `StartModel`、标记类 `Dark` / `Light`。
- [01 ThemeCache](01_ThemeCache/index.md) — `ThemeCache`（全部静态成员）及嵌套类 `InstanceCache`。
- [02 ThemeConfigAttribute](02_ThemeConfigAttribute/index.md) — `ThemeConfigAttribute<TConverter, TTheme...>`（六种元数）与契约 `ITheme`、`IThemeObject`、`IThemeValueConverter`。
- [03 TransitionSystem](03_TransitionSystem/index.md) — 主题功能所驱动的引擎表面：采样器解析、属性与效果契约。
- [04 PlatformAdapters](04_平台适配器/index.md) — 适配器提供的 `Interpolator`、`TransitionEffect` / `TransitionEffects` 与主题值转换器。

## 相关功能

- 过渡动画功能（`2_API/03_transition`）记录了 `ThemeManager` 所驱动的完整动画引擎。
- 各框架的平台接线位于其独立的功能树中（`2_API/08_platform-adapters`）。
