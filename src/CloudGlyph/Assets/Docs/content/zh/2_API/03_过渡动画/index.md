# Transition — API 参考

过渡系统（Transition System）是所有 VeloxDev UI 适配器共享的动画引擎。引擎本体位于 `VeloxDev.Core` 程序集——实现位于 `Src/Core/VeloxDev.Core/TransitionSystem/**`，契约位于 `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/**`——公开 API 横跨四个核心命名空间：

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.TransitionSystem` | 核心契约（`IEaseCalculator`、`ISampler`、`ISampleable`、`ITransitionProperty`、`IFrameState`、`ITransitionEffect*`、`ITransitionScheduler*`、`ITransitionInterpreter<TPriorityCore>`、`IUIThreadInspector<TPriorityCore>` + 共享基接口 `IUIThreadInspectorCore`）、`NonPriority` 标记结构体、两个路径异常（`TransitionPathConflictException` / `TransitionPathUnsampleableException`）、`RotationDirection` 枚举、`Eases` 工厂与各具体缓动类、以及流程扩展 `TransitionCoreEx` |
| `VeloxDev.TransitionSystem.Abstractions` | 引擎基础类型：`TransitionCore`、`StateSnapshotCore` 系列、`StateCore`、`InterpolatorCore`、`SamplerSet<TPriorityCore>`、`TransitionEffectCore`、`TransitionSchedulerCore`、`TransitionInterpreterCore`、`UIThreadInspectorCore`、`TransitionProperty` |
| `VeloxDev.TransitionSystem.NativeSamplers` | 内置无状态采样器（`DoubleSampler`、`QuaternionSampler`、……） |
| `VeloxDev.TimeLine` | `TransitionEventArgs`（及其基类 `TimeLineEventArgs`） |

每个平台适配器——WPF、Avalonia、WinUI、MAUI、WinForms、Razor、Jalium（`Src/Adapters/VeloxDev.*`）——在 `VeloxDev.TransitionSystem` 命名空间中重新暴露相同的公共形态：各自的 `Transition`（非泛型，承载静态 `Exit`）、`Transition<T>`（`Create` / `Property` / `Effect`）、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`、`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`，以及它们注册的平台采样器；流程扩展 `TransitionCoreEx`（`Await` / `Then` / `AwaitThen` / `Interpolator`）由 Core 提供、在各平台共用。

下述成员均对照上述源码验证；行为性论断标注了 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 与 `Examples/Transition/*` 下的示例；凡未被示例或测试证实的签名标记为 *推断所得*。

## 分节

本功能的 API 参考拆分为五节：

- [00_transitionsystem](00_transitionsystem/index.md) — `VeloxDev.TransitionSystem` 核心契约：采样/属性契约、效果-调度-解释器契约、`RotationDirection`、`Eases` 与具体缓动类。
- [01_abstractions](01_abstractions/index.md) — `VeloxDev.TransitionSystem.Abstractions` 中的引擎实现基础类型。
- [02_nativesamplers](02_nativesamplers/index.md) — `VeloxDev.TransitionSystem.NativeSamplers` 中的内置采样器。
- [03_adapter-provided](03_adapter-provided/index.md) — 各适配器在 `VeloxDev.TransitionSystem` 中提供的平台表面。
- [04_timeline](04_timeline/index.md) — `VeloxDev.TimeLine.TransitionEventArgs` 与 `Handled` 取消。
