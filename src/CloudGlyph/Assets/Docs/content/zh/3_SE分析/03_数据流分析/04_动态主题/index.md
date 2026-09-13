# 数据流 — 动态主题

动态主题的数据流分为三个阶段：注册主题感知视图并把其 `[ThemeConfig]` 声明转换为具体值；切换当前主题（带动画时经平台 scheduler 运行，或即时落值）；在运行时覆盖单个属性值。

## 页面

| 页面 | 覆盖的流程 |
|---|---|
| [注册](00_注册/index.md) | `InitializeTheme()` → `ThemeCache.RegisterType` + `ThemeManager.Register` + 应用当前主题；把特性参数转换为具体值的转换器管线 |
| [切换](01_切换/index.md) | `Transition<T>` 准备分组条目并经 `InterpolatorCore.CreateScheduler` 在一条共享 `ITimeSourceControl` 上运行；`Jump<T>` 直接写入全部终值。守卫条件、降级与取消路径 |
| [运行时覆盖](02_运行时覆盖/index.md) | `SetThemeValue<T>` / `RestoreThemeValue<T>`，以及活跃（动态）值如何覆盖静态值 |

> 关键源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`、`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。
