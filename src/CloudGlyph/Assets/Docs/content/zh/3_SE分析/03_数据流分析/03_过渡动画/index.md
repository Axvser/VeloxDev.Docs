# 数据流 — 过渡动画

引擎在每个平台适配器上跑同一条核心流水线。每一趟在段内分**三个阶段**：构建器为该目标解析一个调度器，调度器*准备*出一套归一化的 `SamplerSet`（读当前值、解析采样器、固定端点），随后解释器驱动一条*连续*采样循环，锚定在该趟的时间轴上，并把每一帧写入编组到宿主的线程。本节以 PlantUML 时序图绘出运行生命周期、节拍与 UI 线程跳转，以及错误路径。

## 子页

- [run-lifecycle](00_运行生命周期/index.md) —— `Execute` → 调度器 → `Awake` → `Prepare` → 解释器，以及一个**已准备状态**（每条已声明路径一条 `SamplerSet` 条目）里有什么。
- [pacing-and-marshal](01_节拍与编组/index.md) —— 循环如何决定*何时*采样（时间轴 + `FramePacerCore` / `ReusableTimerWait`），以及每一帧如何被编组到所属线程。
- [error-path](02_错误路径/index.md) —— 当回调、采样器、宿主派发或 `Prepare` 抛异常时会发生什么：`Warn` / `Error` 通道，以及为什么该趟仍经 `Canceled` + `Finally` 收尾。

## 流程汇总

| 场景 | 行为 |
|---|---|
| 正常一趟 | `CoreExecute` 把链上每个分段排队，随后逐段：`await delay` → 调度器 `Execute`（门）→ 宿主线程上的 `Awake` → `Prepare` 为每个属性建一条 `SamplerSet` 条目 → 解释器连续采样并经宿主施加每一帧 → `Completed` + `Finally`。 |
| `IsAutoReverse` | 正向趟之后解释器跑一趟反向（同样的采样器；趟末 `easedT = 0`）。 |
| `LoopTime` / `Repeat` | `LoopTime` 重复一个分段的趟；`Repeat(count)` 重复一个分段的*循环*，包裹从首段到该段的链，并重放首次迭代准备的那套帧集。 |
| 采样节奏 | 时间轴决定一帧*何时*是；`1000 / max(1, FPS)` 毫秒只约束循环多久看一次。停摆的时间轴让循环停摆，于是完全不耗唤醒。 |
| `Pause` / `Resume` / `SetRate` / `Seek` | `Transition.*` 作用于该趟的 `ITimeSourceControl`，**不是**调度器：暂停冻结时钟（暂停时间被排除而非跳过）、变速先重基（因此位置不跳）、定位改写 `run.PassAnchor`（`cycle` 重载还改趟计数器）。 |
| 共享时间轴 | 给了同一个 `ITimeSourceControl` 的两趟共享一套传输，但保留各自的趟与位置，因此一次 `Pause` 把两者都冻结，而一次 `Exit` 只停一个。 |
| 索引实参 | 默认每帧重新求值，因此路径跟随它们，而终值留在它被读取处。`PathIndex.Frozen(i)` 把槽位钉死整条动画，并且是路径身份的一部分。 |
| 反射路径 | `TransitionProperty.FromProperty` 为每个 `PropertyInfo` 返回记忆化的共享路径，因此主题切换不再为每次切换的每个目标重编译 getter 与 setter。 |
| 同目标上新的互斥趟 | `CoreExecute` 先抽干并取消上一趟的 token（推进代计数器）；上一趟在下一个检查点放弃，于是已排队的帧被跳过。 |
| `TransitionEventArgs.Handled = true` | 事件处理器让解释器抛 `OperationCanceledException` → `Canceled` + `Finally`；时间轴停止。 |
| 抛异常的回调 / 采样器 / 宿主 | 经 `Error` 报一次，随后该趟沿它的**正常**取消路径回卷，使 `Canceled` 与 `Finally` 仍然触发、循环资源仍然释放。 |
| 属性无采样器 / 路径无效 | 与目标运行时类型不符的路径在 `Prepare` 被跳过（`UnreadablePath`）并经 `Warn` 报出；一条声明为**引用类型**却无采样器的路径被 `Execute` 拒绝（`TransitionPathUnsampleableException`），而不是当作什么都没动画。其余属性继续动画。 |
| 应用正在关闭 | `SamplerSet.CanSetValue()` 返回 `host.IsAlive == false` → `Apply` 跳过写入且不再触发后续事件。 |

相关分析：[设计模式 — 过渡动画](../../02_设计模式分析/03_过渡动画/index.md) · [复杂度 — 过渡动画](../../04_复杂度分析/03_过渡动画/index.md)
