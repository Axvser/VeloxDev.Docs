# 过渡动画

动画引擎分为 Core（控制面、采样契约、缓动与状态模型）和各 GUI 适配器（帧调度器、解释器、宿主与平台采样器）。一个过渡是一条快照链；适配器里的 `Transition<T>` 是 `TransitionCore<T, …>` 之上的流式前端。

Core 程序集的目标框架为 `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0` 与 `net8.0`。适配器的过渡类型同样位于 `VeloxDev.TransitionSystem`，但由引用该适配器的包提供。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 控制面与链 | `TransitionCore`、`TransitionCore<T, …>`、`StateSnapshotCore<T>`、`StateSnapshotCore`、`StateCore`、`TransitionCoreEx`、`TransitionProperty`、`PathIndex`、路径异常 | [过渡核心](00_过渡核心/index.md) |
| 效果与缓动 | `ITransitionEffectCore`、`ITransitionEffect<TPriorityCore>`、`TransitionEffectCore`、`TransitionEffectCore<TPriorityCore>`、`IEaseCalculator`、`Eases` 及其曲线类 | [效果与缓动](01_效果与缓动/index.md) |
| 采样 | `ISampler`、`ISampleable`、`InterpolatorCore`、`ITransitionProperty`、`IFrameState`、`SamplerSet<TPriorityCore>`、`BoundedProgress`、`RotationDirection`、内置采样器 | [采样](02_采样/index.md) |
| 调度与事件 | `ITransitionSchedulerCore`、`ITransitionScheduler`、`ITransitionScheduler<TPriorityCore>`、`FramePacerCore`、`TransitionSchedulerCore`、`TransitionInterpreterCore`、`ITransitionHost<TPriorityCore>`、`TransitionHostBase<TPriorityCore>` | [调度与事件](03_调度与事件/index.md) |
| 平台适配类型 | `Transition`、`Transition<T>`、`State`、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector` | [平台适配类型](04_平台适配类型/index.md) |

## 典型流程

1. 构建链：`Transition<T>.Create()`，然后为每个动画值调用 `Property(lambda, endValue, options?)`，并用 `Effect(...)` 设置时序。
2. 可选地用 `Then()`、`Await(TimeSpan)`、`AwaitThen(TimeSpan)` 与 `Repeat(int)` 扩展链。
3. 用 `Execute(target, CanMutualTask)` 或针对共享时间轴运行。
4. 按目标控制运行：`Transition.Pause`、`Resume`、`SetRate`、`Seek`、`Exit`、`Position`、`Cycle`、`IsPaused`。

可运行的 WPF 窗口见[过渡动画快速开始](../../1_快速开始/12_过渡动画/index.md)。

## 异常

| 异常 | 抛出方 |
|---|---|
| `TransitionPathUnsampleableException` | 链校验时，声明的路径终结于无采样器的引用类型。 |
| `TransitionPathConflictException` | `StateCore.SetValue` 中，路径位于已声明路径之上或之下。 |
| `InvalidOperationException` | 链接收错误类型的段。 |
| `ArgumentOutOfRangeException` | `SetRate` 收到负速率。 |
