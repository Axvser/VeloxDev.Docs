# 过渡动画 — 快速开始

## 概述

**过渡动画**（Transition）是 VeloxDev 的跨平台、代码驱动插值引擎。它的核心思想是**「一切都是状态」**：你逐路径声明对象应当到达的状态（`Transition<T>.Create().Property(x => x.Foo, value)`）然后执行 —— 引擎在该趟开始时读取每个已声明属性的**当前值**，在一条按时间、经缓动、按帧推进的时间轴上把它插值到声明的目标。没有捕获步骤：不从活对象上发现或记录任何东西。

引擎分三层：

- **引擎内核**（`VeloxDev.Core`）—— `VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions` 下的与框架无关的类型：`Eases` 与 `Ease*` 类、`TransitionEffectCore`（时长 / FPS / 缓动 / 循环 / 事件）、`InterpolatorCore`（采样器注册表 + `NativeSamplers/*`）、按目标的 `TransitionSchedulerCore`、带 `FramePacerCore` 节奏接缝的帧循环 `TransitionInterpreterCore`、抽象类 `TransitionHostBase<TPriorityCore>`、`BoundedProgress`、路径异常，以及开放泛型构建器基类 `TransitionCore<...>` / `StateSnapshotCore<...>`。
- **时间层**（`VeloxDev.Timing` + `VeloxDev.Threading` / `VeloxDev.Lifetime`，都在 `VeloxDev.Core` 内）—— 每一趟锚定的时钟（`ITimeSource` / `ITimeSourceControl`），以及回答「哪个线程」与「应用是否还活着」的宿主接缝（`ITransitionHost<TPriorityCore>`）。见[时间层](07_时间层/index.md)。
- **GUI 适配器层**（平台适配器包，如 `VeloxDev.WPF`）—— 在单一命名空间 `VeloxDev.TransitionSystem` 下重新给出友好、封闭的类型：`Transition`、`Transition<T>`（静态入口*兼*流式构建器与执行器）、`State`、`TransitionEffect`、`TransitionEffects`（Empty / Theme / Hover 预设）、`Interpolator`（静态构造函数里注册的平台采样器）、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector`（适配器宿主），加上 Core 侧的 `TransitionCoreEx` 链式扩展（`Await` / `Then` / `AwaitThen` / `Repeat` / `Interpolator`）。

动画化 **UI 绑定属性**需要你 GUI 框架对应的适配器包：它带来按框架的值采样器（`Brush`、`Color`、`Transform` 等）并把每一帧写入编组到 UI 线程。动画化**纯非 UI 值**不需要适配器 —— 引擎内核类型可无头运行（见[安装依赖](01_安装依赖/index.md)），而时间层本身就能独立无头运行（[时间层](07_时间层/index.md)）。

权威示例位于 `Examples/Transition/*`（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium）。引擎契约有两重钉死：`Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 与 `Src/Core/VeloxDev.Core.Test/Timing/*` 的单元测试（285 条），以及 **`Examples/Transition/AUTO TEST`** 一致性验收套件 —— 它通过 UI Automation 与浏览器驱动全部七个真实演示，并把采样器算术与一份独立写就的闭式解对照。

## 快速开始 —— 子页

- [00 前置条件](00_前置条件/index.md) —— 支持的目标框架、SDK/工作负载、各演示与 `AUTO TEST` 套件
- [01 安装依赖](01_安装依赖/index.md) —— `VeloxDev.Core` + 用于 UI 绑定属性的平台适配器包
- [02 缓动与插值器](02_缓动与插值器/index.md) —— 内置缓动目录、自定义 `IEaseCalculator`、自定义 `ISampler` 注册
- [03 声明状态](03_声明状态/index.md) —— 用 `Transition<T>.Create().Property(...)` 逐路径声明目标值，并把重置表达成一次零时长写回
- [04 分段与循环](04_分段与循环/index.md) —— 多段timeline、自动反向/循环、链级 `Repeat(n)`、FPS 上限、效果事件与诊断、预设
- [05 执行与控制](05_执行与控制/index.md) —— 一次性执行、互斥与并发、共享时间轴、退出、暂停 / 变速 / 定位、按目标调度器
- [06 UI线程与编组](06_UI线程与编组/index.md) —— 各平台宿主接线与线程编组契约
- [07 时间层](07_时间层/index.md) —— 无头驱动 `VeloxDev.Timing`：时间源、两种采样模式、停摆信号
- [08 验证与完整代码](08_验证与完整代码/index.md) —— 演示、`AUTO TEST` 套件、单一可运行程序，以及运行声明
