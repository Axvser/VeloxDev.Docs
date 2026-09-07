# 数据流 — 动态主题

动态主题的数据流分为三个阶段：注册主题感知视图并把其 `[ThemeConfig]` 声明转换为具体值；经由共享采样器管线切换当前主题（带动画或即时）；在运行时覆盖单个属性值。

## 页面

| 页面 | 覆盖的流程 |
|---|---|
| [注册](00_注册/index.md) | `InitializeTheme()` → `ThemeCache.RegisterType` + `ThemeManager.Register` + 应用当前主题；把特性参数转换为具体值的转换器管线 |
| [切换](01_切换/index.md) | `Transition<T>` 带动画切换与 `Jump<T>` 即时切换，共享 `PrepareSamplers` + `ExecuteTransition`；守卫条件与边界路径 |
| [运行时覆盖](02_运行时覆盖/index.md) | `SetThemeValue<T>` / `RestoreThemeValue<T>`，以及活跃（动态）值如何覆盖静态值 |

> 关键源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。
