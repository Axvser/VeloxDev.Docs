# 过渡动画 — 核心契约：`VeloxDev.TransitionSystem`

本节记录动画引擎与 UI 无关的核心契约。它们声明在 `VeloxDev.Core` 程序集的 `VeloxDev.TransitionSystem` 命名空间（源：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs` 与 `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`），从不引用任何平台类型。平台适配器以具体类型实现这些契约，见 [adapter-provided](../03_适配器提供/index.md)。

## 职责划分

引擎把六件事分开，每件以一个接口表达：

- **采样** —— `ISampler` 按归一化时间插值一个属性；`ISampleable` 让**值类型**声明自己的可动画成员（结构体装配），无需注册采样器。
- **属性寻址** —— `ITransitionProperty` 命名一条（可能嵌套的）属性路径；`IFrameState` 是一次过渡所声明的值 / 采样器 / 选项的容器。
- **时间描述** —— `IEaseCalculator`、`ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>` 描述单趟动画的行为。
- **执行** —— `ITransitionSchedulerCore` 按目标串行化动画；`ITransitionInterpreter<TPriorityCore>` 跑采样循环；`FramePacerCore` 决定循环下一帧何时发生。没有调度器优先级的宿主把 `TPriorityCore` 填为 `NonPriority`。
- **宿主 / UI 编组** —— `ITransitionHost<TPriorityCore>` 是引擎向宿主索取的全部：目标属于哪个线程（`IThreadAffinity`）、如何把工作送过去（`IThreadDispatcher<TPriorityCore>`）、宿主是否还在运行（`IApplicationState`）。它是**组合**，不是新契约 —— 不新增任何成员。
- **时钟** —— 引擎从 `VeloxDev.Timing` 的 `ITimeSource` 读时间，而不读框架时钟。该层有独立分节：[timing](../05_timing/index.md)。

本命名空间的其余成员 —— `RotationDirection` 枚举与 `Eases` 工厂 / 具体缓动类 —— 与采样契约同列。

## 子页

- [sampling-capture](00_采样与捕获/index.md) —— `ISampler`、`ISampleable`、`ITransitionProperty`、`IFrameState`（采样与属性寻址契约）、`BoundedProgress` 分组助手，以及两个路径异常。
- [effect-engine](01_效果引擎/index.md) —— `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>`、调度器与解释器接口，以及 `FramePacerCore` 节奏基类。
- [eases](02_eases/index.md) —— `RotationDirection`、`Eases` 及 31 个具体缓动类。
- [host](03_宿主/index.md) —— 宿主线程契约：`ITransitionHost<TPriorityCore>`、`IThreadAffinity`、`IThreadDispatcher<TPriorityCore>`、`ThreadRef`、`NonPriority`、`IApplicationState`，以及 `ThreadDispatcherBase<TPriorityCore>` 基类。
