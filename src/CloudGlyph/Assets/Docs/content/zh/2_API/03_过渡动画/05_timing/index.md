# 过渡动画 — 子模块：`VeloxDev.Timing`

过渡引擎读取的时钟。它是过渡特性的一个**子模块**而不是独立特性：`VeloxDev.Timing`（`Src/Core/VeloxDev.Core/Timing/**` + `Interfaces/Timing/**`，首次加入于 2026-09-14）是关键字级的基础设施，由 transition / dynamic-theme / tickable 共享，而过渡系统是它第一个也最重的消费者。`dynamic-theme` 特性经一次主题切换触达它，`tickable` 特性经 `TickManager` 触达它。

每个动画锚定在一个 `ITimeSource` 上，而不是锚定在框架时钟上：`TransitionRun.Timeline` 就是这样一个源，所有控制调用（`Pause`、`Resume`、`SetRate`、`Seek`）都作用于它。正是它让多个动画共享一套传输，也正是它使「不能用那种方式驱动」成为源自身的性质、而不是每个消费者的性质。

## 它为什么存在

框架自己的时钟给不了引擎的三件事，而之前的设计必须逐平台重新推演：

- **暂停是被排除的，不是被跳过的。** `Stopwatch` 在一个标志说「别计数」时仍继续走；一个暂停期间干脆不前进的源，使这种排除成为构造性的，并去掉了旧设计里恢复后的 delta 尖峰。
- **一趟可以停摆。** 消费者在 `WaitWhileStalledAsync` 上等待而不是轮询，因此暂停或冻结的动画**完全不耗定时器唤醒**。
- **时间是共享的。** 多个消费者可以锚定在同一个源上，因此一次暂停会同时停下帧循环与跑在它上面的动画。

## 子页

- [contracts](00_契约/index.md) —— `TimeSample`、`ITimeSource`、`ITimeSourceControl`、`ITimeSampler`、`IUncompensatedTimeSampler`、`ICompensatingTimeSampler`。
- [implementation](01_实现/index.md) —— `TimeConversion`、`TimeSourceCore`、`UncompensatedTimeSampler`、`CompensatingTimeSampler`，以及 `TimerCore` 注册表。

## 引擎在哪里与它相遇

| 引擎类型 | 它如何使用时间层 |
|---|---|
| `Abstractions.TransitionRun` | 持有该趟锚定的 `ITimeSourceControl`、`PassAnchor`（当前趟在该源中的起点）与 `Cycle` 计数器 |
| `Abstractions.TransitionInterpreterCore` | 读 `timeline.Ticks` 取趟位置、读 `timeline.IsAdvancing` 决定是否「先画后停」、用 `TimeConversion.TicksToMilliseconds` 换算、以 `timeline.TicksPerSecond` 为单位 |
| `TransitionCore.Seek` / `Position` | 用 `TimeConversion` 在 `TimeSpan` 与源的 tick 单位间换算，并改写 `run.PassAnchor` |
| `TransitionCore.Pause` / `Resume` / `SetRate` | 把调用转给 `run.Timeline` |
| `Abstractions.SamplerSet`（测试直接驱动解释器时） | 回退到 `TimerCore.CreateTimeSource<ITimeSourceControl>()`，得到自己那条私有的、不可控的 run |
| `TransitionCore.ExecuteCoreAsync` | 调用方没提供源时，用 `TimerCore.CreateTimeSource<ITimeSourceControl>()` 建默认源 |
