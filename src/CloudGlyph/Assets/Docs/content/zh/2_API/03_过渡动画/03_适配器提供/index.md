# 过渡动画 — 适配器提供的表面

每个平台适配器（`Src/Adapters/VeloxDev.WPF|Avalonia|WinUI|MAUI|WinForms|Razor|Jalium`）在自己的程序集里、**同一个** `VeloxDev.TransitionSystem` 命名空间中提供一整套具体类型，派生自 [abstractions](../01_abstractions/index.md) 的引擎基类。因此 `using VeloxDev.TransitionSystem;` 的程序在每个平台上看到同一套 API；只有平台值类型不同。

## 各适配器提供什么

| 类型 | 职责 | 派生自 |
|---|---|---|
| `Transition` | 非泛型静态入口（取消 / 退出 / 控制助手） | `TransitionCore` |
| `Transition<T>` | 泛型入口、流式构建器与执行器集于一身（`Create` / `Property` / `Effect`，加上继承来的 `Execute` / 控制方法 / `GetState`） | `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` |
| `Interpolator` | 平台采样器注册表（`InterpolatorCore` 的子类，静态构造函数注册平台类型） | `InterpolatorCore` |
| `State` | 已声明状态容器 | `StateCore` |
| `TransitionEffect` | 带平台默认优先级的时间描述符 | `TransitionEffectCore` 或 `TransitionEffectCore<TPriorityCore>` |
| `TransitionEffects` | `Empty` / `Theme` / `Hover` 预设 | 静态类（WinUI 上是普通类） |
| `UIThreadInspector` | 适配器的**宿主**：线程归属 + 派发 + 存活 | `TransitionHostBase<TPriorityCore>` |
| `TransitionScheduler` | 按目标调度器 | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, TPriorityCore>` |
| `TransitionInterpreter` | 采样循环解释器（及其 `FramePacerCore` 重写） | `TransitionInterpreterCore<TransitionEffect[, TPriorityCore]>` |
| 平台采样器 | 注册的值类型插值器 | `ISampler`（各适配器内的命名空间 `VeloxDev.Adapters.NativeSamplers`） |

带优先级的适配器（WPF、Avalonia、Jalium、WinUI）以某个调度器优先级编组写入；MAUI、WinForms、Razor 无优先级。

| 适配器 | 框架 | 优先级类型 | 优先级默认值 |
|---|---|---|---|
| WPF | `System.Windows.Threading` | `DispatcherPriority` | `DispatcherPriority.Render` |
| Avalonia | Avalonia | `DispatcherPriority` | `DispatcherPriority.Render` |
| Jalium | Jalium | `DispatcherPriority` | `DispatcherPriority.Render` |
| WinUI | Microsoft.UI | `DispatcherQueuePriority` | `DispatcherQueuePriority.High` |
| MAUI | .NET MAUI | ——（无优先级） | —— |
| WinForms | System.Windows.Forms | —— | —— |
| Razor | Blazor / Razor | —— | —— |

## 子页

- [transition](00_transition/index.md) —— `Transition`、`Transition<T>`（`Property` / `Effect` 重载集，以及继承来的 `Execute` / 控制 / `GetState` 表面）。
- [effect-interpolator](01_效果插值器/index.md) —— `Interpolator` 及其各适配器采样器注册、`TransitionEffect`（含 `Warn` / `Error` 诊断事件）、`TransitionEffects`，以及 `State`。
- [ui-inspector](02_UI线程检查器/index.md) —— 各平台的 `UIThreadInspector`（适配器宿主），以及 `TransitionScheduler` / `TransitionInterpreter` 适配器子类。
