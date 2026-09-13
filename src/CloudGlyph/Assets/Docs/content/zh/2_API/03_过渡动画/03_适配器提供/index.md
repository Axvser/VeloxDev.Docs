# Transition — 适配器提供的表面

每个平台适配器（`Src/Adapters/VeloxDev.WPF|Avalonia|WinUI|MAUI|WinForms|Razor|Jalium`）在自己的程序集里、且在**同一个** `VeloxDev.TransitionSystem` 命名空间中提供一组具体类型，子类化 [01_abstractions](../01_abstractions/index.md) 的引擎基础类型。因此 `using VeloxDev.TransitionSystem;` 的程序在每个平台上看到统一 API——只有平台值类型不同。

## 每个适配器提供什么

| 类型 | 角色 | 派生自 |
|---|---|---|
| `Transition` | 非泛型入口（承载静态 `Exit`） | `TransitionCore` |
| `Transition<T>` | 流式构建器 + 泛型入口（`Create` / `Property` / `Effect`） | 7 元数 `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` |
| `TransitionCoreEx`（Core 提供） | 流程扩展：`Await` / `Then` / `AwaitThen` / `Interpolator` | 静态类 |
| `Interpolator` | 平台采样器注册表（子类 `InterpolatorCore` 并在静态构造注册平台类型） | `InterpolatorCore` |
| `State` | 分段的状态集合 | `StateCore` |
| `TransitionEffect` | 时序描述符，适用时带默认优先级 | `TransitionEffectCore` 或 `TransitionEffectCore<TPriorityCore>` |
| `TransitionEffects` | `Empty` / `Theme` / `Hover` 预设 | 静态类（WinUI 上为实例类） |
| `UIThreadInspector` | 平台 UI 线程编组 | `UIThreadInspectorCore` 或 `UIThreadInspectorCore<TPriorityCore>` |
| `TransitionScheduler` | 按目标调度器 | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter[, TPriorityCore]>` |
| `TransitionInterpreter` | 采样循环解释器 | `TransitionInterpreterCore<TransitionEffect[, TPriorityCore]>` |
| 平台采样器 | 已注册的值类型插值器 | `ISampler`（各适配器内命名空间 `VeloxDev.Adapters.NativeSamplers`） |

优先级类型化适配器（WPF、Avalonia、Jalium、WinUI）以 dispatcher 优先级编组写入；MAUI、WinForms 与 Razor 无优先级。

| 适配器 | 框架 | 优先级类型 | 优先级默认 |
|---|---|---|---|
| WPF | `System.Windows.Threading` | `DispatcherPriority` | `DispatcherPriority.Render` |
| Avalonia | Avalonia | `DispatcherPriority` | `DispatcherPriority.Render` |
| Jalium | Jalium | `DispatcherPriority` | `DispatcherPriority.Render` |
| WinUI | Microsoft.UI | `DispatcherQueuePriority` | `DispatcherQueuePriority.High` |
| MAUI | .NET MAUI | —（无优先级） | — |
| WinForms | System.Windows.Forms | — | — |
| Razor | Blazor / Razor | — | — |

## 子页

- [00_transition](00_transition/index.md) — `Transition` 与 `Transition<T>`（含 `Property` / `Effect` 重载集）。
- [01_effect-interpolator](01_效果插值器/index.md) — `Interpolator` 及其各适配器采样器注册、`TransitionEffect`、`TransitionEffects` 与 `State`。
- [02_ui-inspector](02_UI线程检查器/index.md) — 各适配器的 `UIThreadInspector`，以及 `TransitionScheduler` / `TransitionInterpreter` 适配器子类。
