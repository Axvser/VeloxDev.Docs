# 过渡动画 — 快速开始

## 概述

**过渡动画**是 VeloxDev 跨平台、代码驱动的插值引擎。它的核心思想是**「一切都是状态」**：你逐路径声明对象应当到达的状态（`Transition<T>.Create().Property(x => x.Foo, value)`），然后执行 —— 引擎在运行开始时读取每条已声明属性的当前值，并在有时长、有缓动、基于帧的时间轴上把它插值到声明目标。这里**没有捕获步骤**：引擎不会从活动对象发现或记录任何东西。

引擎分三层：

- **引擎核心**（`VeloxDev.Core`）—— 与框架无关的类型，位于 `VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`：`Eases` 与 `Ease*` 类、`TransitionEffectCore`（时长 / FPS / 缓动 / 循环 / 事件）、`InterpolatorCore`（采样器注册表 + `NativeSamplers/*`）、按目标划分的 `TransitionSchedulerCore`、带 `FramePacerCore` 节拍接缝的 `TransitionInterpreterCore`、抽象宿主基类 `TransitionHostBase<TPriorityCore>`、`BoundedProgress`、路径异常，以及开放泛型构建器 `TransitionCore<...>` 及其 `StateSnapshotCore<T>` 执行基类。
- **时间层**（`VeloxDev.Timing` 与 `VeloxDev.Threading` / `VeloxDev.Lifetime`，都在 `VeloxDev.Core` 内）—— 每一趟锚定的时钟（`ITimeSource` / `ITimeSourceControl`）与宿主接缝（`ITransitionHost<TPriorityCore>`），后者回答「哪个线程」和「应用是否还活着」。见[时间层](07_时间层/index.md)。
- **GUI 适配器层**（平台适配器包，如 `VeloxDev.WPF`）—— 在单一命名空间 `VeloxDev.TransitionSystem` 下重新导出友好、封闭的类型：`Transition`、`Transition<T>`（静态入口 *兼* 流式构建器 *兼* 执行器）、`State`、`TransitionEffect`、`TransitionEffects`（Empty / Theme / Hover 预设）、`Interpolator`（在静态构造函数中注册各框架采样器）、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector`（适配器宿主），以及 Core 侧的 `TransitionCoreEx` 链式扩展（`Await` / `Then` / `AwaitThen` / `Repeat` / `Interpolator`）。

动画 **UI 绑定属性**需要对应 GUI 框架的适配器包：它带来该框架的值采样器（`Brush`、`Color`、`Transform` 等），并把每一帧写入编组到 UI 线程。动画 **纯非 UI 值**不需要适配器 —— 引擎核心类型可以无界面运行（见[安装](01_安装/index.md)），时间层也可以独立无界面运行（见[时间层](07_时间层/index.md)）。

权威示例位于 `Examples/Transition/*`（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium）。引擎契约由两层证据钉住：`Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 与 `Src/Core/VeloxDev.Core.Test/Timing/*` 中的单元测试（287 个测试用例），以及 **`Examples/Transition/AUTO TEST`** 一致性验收套件 —— 它通过 UI Automation 和浏览器驱动全部七个真实 demo，并用独立写就的闭式解核对采样器算术。

## 快速开始子页面

- [00 前置条件](00_前置条件/index.md) —— 支持的目标框架、SDK/工作负载、demo 与 `AUTO TEST` 套件
- [01 安装](01_安装/index.md) —— `VeloxDev.Core` + UI 绑定属性所需的平台适配器包
- [02 缓动与插值器](02_缓动与插值器/index.md) —— 内置缓动目录、自定义 `IEaseCalculator`、自定义 `ISampler` 注册
- [03 声明状态](03_声明状态/index.md) —— 用 `Transition<T>.Create().Property(...)` 逐路径声明目标值，并把重置表达为零时长写回
- [04 序列与重复](04_序列与重复/index.md) —— 多段链、自动反向 / 循环、链级 `Repeat(n)`、FPS 上限、效果事件与诊断、预设
- [05 执行与控制](05_执行与控制/index.md) —— 一次性执行、互斥与并发、共享时间轴、退出、暂停 / 速率 / 定位、按目标调度器
- [06 UI线程与编组](06_UI线程与编组/index.md) —— 各平台宿主接线与线程编组契约
- [07 时间层](07_时间层/index.md) —— 无界面驱动 `VeloxDev.Timing`：时间源、两种采样模式与停泊信号
- [08 验证与完整代码](08_验证与完整代码/index.md) —— demo、`AUTO TEST` 套件、单个可运行程序与运行声明
