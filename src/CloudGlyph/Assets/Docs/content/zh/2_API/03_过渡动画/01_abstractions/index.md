# 过渡动画 — 引擎实现：`VeloxDev.TransitionSystem.Abstractions`

命名空间 `VeloxDev.TransitionSystem.Abstractions`，位于 `VeloxDev.Core` 程序集（源：`Src/Core/VeloxDev.Core/TransitionSystem/*.cs`）。这些具体 / 抽象基类实现 [transitionsystem](../00_transitionsystem/index.md) 中记录的契约。每个平台适配器派生它们，产出你实际构造的 `VeloxDev.TransitionSystem` 类型（见 [adapter-provided](../03_适配器提供/index.md)）。

## 命名空间地图

| 类型家族 | 职责 |
|---|---|
| `TransitionCore`（静态入口）与 `TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>`（构建器 + 执行器） | 描述目标状态与分段链，然后运行它 |
| `StateSnapshotCore` / `StateSnapshotCore<T>` | 抽象构建器根；`Execute` 重载与逐实例控制方法 |
| `StateCore : IFrameState` | 已声明状态容器（值 / 采样器 / 选项） |
| `InterpolatorCore` | 采样器注册表、`CreateScheduler` 平台接缝，与 `Prepare` |
| `SamplerSet<TPriorityCore>` | 解释器驱动的、已准备就绪的逐属性采样容器 |
| `TransitionEffectCore[<TPriorityCore>]` | 带生命周期与诊断事件的时间描述符 |
| `TransitionSchedulerCore[<THost, TTransitionInterpreterCore, TPriorityCore>]` | 按目标的执行协调器及其注册表 |
| `TransitionInterpreterCore[<…>]` | 由时间轴驱动的采样循环及其节奏接缝 |
| `TransitionHostBase<TPriorityCore>` | 适配器宿主派生的基类（见 [host](../00_transitionsystem/03_宿主/index.md)） |
| `TransitionProperty` | 编译后的属性路径（state 的键身份） |

下文标注为 *internal* 的类型（`TransitionRun`、`TransitionDiagnostics`、`StructAssembler`、`ReusableTimerWait`、`PathSegment` 及其子类、索引实参家族）不是公开 API，但其行为可观测，各自记于使用它的类型旁。

## 子页

- [builder](00_构建器/index.md) —— `TransitionCore`、`TransitionCore<…>`、`StateSnapshotCore` / `StateSnapshotCore<T>`（含共享时间轴 `Execute` 重载与 `Repeat` 循环语义）、`TransitionCoreEx`、`StateCore`。
- [engine](01_引擎/index.md) —— `InterpolatorCore`、`SamplerSet<TPriorityCore>`、`TransitionEffectCore[<…>]`、`TransitionSchedulerCore[<…>]`（及 `ExecuteCapturing` / `Replay`）、`TransitionInterpreterCore[<…>]`，以及 `TransitionRun`、`TransitionDiagnostics`、`ReusableTimerWait`。
- [paths](02_路径/index.md) —— `TransitionProperty`、`PathIndex` 与 `PathIndex.Frozen`，以及两个路径守卫。
