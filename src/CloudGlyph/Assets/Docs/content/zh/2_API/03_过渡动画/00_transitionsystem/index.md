# Transition — 核心契约：`VeloxDev.TransitionSystem`

本页记录动画引擎的核心、与 UI 无关的契约。它们声明于 `VeloxDev.Core` 程序集的 `VeloxDev.TransitionSystem` 命名空间（源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs` 与 `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`），不引用任何平台类型。平台适配器以具体类型实现这些契约，见 [03_adapter-provided](../03_adapter-provided/index.md)。

## 职责划分

引擎把关注点拆成五个方面，各以接口表达：

- **采样** — `ISampler` 在归一化时间点上插值单个属性；`ISampleable` 让自定义类型自行声明可动画成员（结构体重组）而无需注册采样器。
- **属性寻址** — `ITransitionProperty` 表示（可能嵌套的）属性路径；`IFrameState` 是某个快照的记录值 / 采样器 / 选项的集合。
- **时序** — `IEaseCalculator`、`ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>` 描述单程动画如何表现。
- **执行** — `ITransitionSchedulerCore` 按目标串行化动画；`ITransitionInterpreterCore` 运行采样循环。
- **UI 编组** — `IUIThreadInspectorCore` 回答线程相关问题并把读写编组到 UI 线程。

本命名空间其余成员——`RotationDirection` 枚举与 `Eases` 工厂 / 具体缓动类——与采样契约同页列出。

## 子页

- [00_sampling-capture](00_sampling-capture/index.md) — `ISampler`、`ISampleable`、`ITransitionProperty`、`IFrameState`（采样 + 属性捕获契约）。
- [01_effect-engine](01_effect-engine/index.md) — `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>`、调度器与解释器接口、`IUIThreadInspectorCore`。
- [02_eases](02_eases/index.md) — `RotationDirection`、`Eases` 与 31 个具体缓动类。
