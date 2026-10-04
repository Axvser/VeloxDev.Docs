# 过渡动画 — API 参考

过渡动画系统是全部 VeloxDev UI 适配器共用的动画引擎。引擎本体位于 `VeloxDev.Core` 程序集 —— 实现位于 `Src/Core/VeloxDev.Core/TransitionSystem/**`，契约位于 `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/**` —— 并且自 2026-09-14 起建立在另外两个 Core 子系统之上：时间层（`VeloxDev.Timing`，`Src/Core/VeloxDev.Core/Timing/**` + `Interfaces/Timing/**`）与线程/宿主层（`VeloxDev.Threading`、`VeloxDev.Lifetime`）。它的公开 API 跨以下命名空间：

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.TransitionSystem` | 核心契约（`IEaseCalculator`、`ISampler`、`ISampleable`、`ITransitionProperty`、`IFrameState`、`ITransitionEffect*`、`ITransitionScheduler*`、`ITransitionInterpreter*`、`ITransitionHost<TPriorityCore>`）、`RotationDirection` 枚举、`BoundedProgress` 结构、抽象类 `FramePacerCore`、路径异常（`TransitionPathConflictException`、`TransitionPathUnsampleableException`）、`PathIndex`、`Eases` 工厂及其 31 个缓动类，以及 `TransitionCoreEx` 链式扩展 |
| `VeloxDev.TransitionSystem.Abstractions` | 引擎基类：`TransitionCore`、`StateSnapshotCore` 家族、`StateCore`、`InterpolatorCore`、`SamplerSet<TPriorityCore>`、`TransitionEffectCore[<TPriorityCore>]`、`TransitionSchedulerCore`、`TransitionInterpreterCore`、`TransitionHostBase<TPriorityCore>`、`TransitionProperty` |
| `VeloxDev.TransitionSystem.NativeSamplers` | 内置无状态采样器（`DoubleSampler`、`QuaternionSampler` 等） |
| `VeloxDev.Timing` | 共享时钟：`ITimeSource` / `ITimeSourceControl`、两种采样契约（`IUncompensatedTimeSampler`、`ICompensatingTimeSampler`）及其 `TimeSample`、默认实现（`TimeSourceCore`、`UncompensatedTimeSampler`、`CompensatingTimeSampler`）、`TimeConversion` 换算，以及 `TimerCore` 注册表 |
| `VeloxDev.Threading` | 宿主的线程面：`IThreadAffinity`、`IThreadDispatcher<TPriorityCore>`、`ThreadDispatcherBase<TPriorityCore>`、`ThreadRef`、`NonPriority` |
| `VeloxDev.Lifetime` | `IApplicationState` 与 `ApplicationState` 存活标志 |
| `VeloxDev.TimeLine` | `TransitionEventArgs`（携带 `Stage` / `Message` / `Exception`）及其基类 `TimeLineEventArgs` |

每个平台适配器 —— WPF、Avalonia、WinUI、MAUI、WinForms、Razor、Jalium（`Src/Adapters/VeloxDev.*`）—— 在 `VeloxDev.TransitionSystem` 命名空间中重新给出同样的公开形状：自己的 `Transition`、`Transition<T>`（静态入口、流式构建器与执行器集于一身）、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`、`UIThreadInspector`（适配器的 `TransitionHostBase<TPriorityCore>` 子类）、`TransitionScheduler`、`TransitionInterpreter`，以及它注册的平台采样器。各适配器自身的派生细节 —— 适配器包、模板与附加行为 —— 属于**特性 08**：见[平台适配器](../08_平台适配器/index.md)。

下列成员均已对照上述源文件核验。行为性论断引用 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*`、`Src/Core/VeloxDev.Core.Test/Timing/*`、`Examples/Transition/AUTO TEST` 一致性验收套件与 `Examples/Transition/*` 下的演示；未经演示、测试或套件确认的签名标注为 *inferred*。

## 分节

本特性的 API 参考分为六节：

- [transitionsystem](00_transitionsystem/index.md) —— `VeloxDev.TransitionSystem` 核心契约：采样/属性契约、效果-调度器-解释器契约、宿主线程契约、`RotationDirection`、`BoundedProgress`、`FramePacerCore`、`Eases` 及具体缓动类。
- [abstractions](01_abstractions/index.md) —— `VeloxDev.TransitionSystem.Abstractions` 中的引擎实现基类。
- [nativesamplers](02_nativesamplers/index.md) —— `VeloxDev.TransitionSystem.NativeSamplers` 中的内置采样器。
- [adapter-provided](03_适配器提供/index.md) —— 各适配器在 `VeloxDev.TransitionSystem` 中提供的平台面。
- [timeline](04_timeline/index.md) —— `VeloxDev.TimeLine.TransitionEventArgs` 与 `Handled` 取消。
- [timing](05_timing/index.md) —— 帧循环与过渡引擎共享的 `VeloxDev.Timing` 时钟。
