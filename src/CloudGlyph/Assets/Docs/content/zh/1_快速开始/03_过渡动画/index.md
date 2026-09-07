# Transition — 快速入门

## Transition

### 概述

**Transition** 是 VeloxDev 的跨平台、代码驱动插值引擎。核心思想是**「一切皆状态」**：把目标的属性值记录为*状态快照*，描述对象应到达的最终状态，然后执行 —— 引擎把每个记录的属性从当前值插值到目标值，经过一条定时、带缓动、按帧的时间线。

引擎分为两层：

- **引擎核心**（`VeloxDev.Core`）—— 与 UI 框架无关的类型，位于 `VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`：`Eases` 与 `Ease*` 类、`TransitionEffectCore`（时长 / FPS / 缓动 / 循环 / 事件）、`InterpolatorCore`（采样器注册表 + `NativeInterpolators`）、`NativeSamplers/*` 内置采样器、按目标的 `TransitionSchedulerCore`、帧循环 `TransitionInterpreterCore`、抽象 `UIThreadInspectorCore` 以及开放泛型快照机制（`TransitionCore<...>` / `StateSnapshotCore<...>`）。
- **GUI 适配器层**（平台适配器包，例如 `VeloxDev.WPF`）—— 在统一命名空间 `VeloxDev.TransitionSystem` 下重新导出封闭的便捷类型：`Transition` / `Transition<T>.StateSnapshot`、`State`、`TransitionEffect`、`TransitionEffects`（Empty / Theme / Hover 预设）、`Interpolator`（其静态构造函数注册各框架采样器）、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector`，以及 `TransitionEx` 快照扩展（`Snapshot` / `SnapshotAll` / `SnapshotExcept`）。

**动画 UI 绑定的属性**需要对应 GUI 框架的适配器包：它带来框架专属的值采样器（`Brush`、`Color`、`Transform` …）并把每一帧写入编组到 UI 线程。**动画纯的非 UI 值**无需适配器 —— 引擎核心类型可无界面运行（见 [安装依赖](01_安装依赖/index.md)）。

权威示例位于 `Examples/Transition/*`（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium）；引擎契约由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 锁定。

## 快速入门 — 子页面

- [00 前置条件](00_前置条件/index.md) — 支持的目标框架、SDK/工作负载、示例
- [01 安装依赖](01_安装依赖/index.md) — `VeloxDev.Core` + 面向 UI 绑定属性的平台适配器包
- [02 缓动与插值器](02_缓动与插值器/index.md) — 内置缓动目录、自定义 `IEaseCalculator`、自定义 `ISampler` 注册
- [03 定义状态快照](03_定义状态快照/index.md) — 记录属性目标值与效果；捕获对象当前状态
- [04 分段与循环](04_分段与循环/index.md) — 多段时间线、自动往返/循环、FPS 上限、效果事件、预设
- [05 执行与控制](05_执行与控制/index.md) — 一次性执行、互斥与并行、退出、按目标调度器
- [06 UI线程与编组](06_UI线程与编组/index.md) — 各平台 UI 线程接线与 `CaptureUIThread`
- [07 验证与完整代码](07_验证与完整代码/index.md) — 示例与测试、单个可运行程序、运行声明
