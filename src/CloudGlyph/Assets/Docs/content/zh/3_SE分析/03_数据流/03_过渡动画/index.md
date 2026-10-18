# 数据流 — 过渡动画

引擎在每个平台适配器上运行同一条核心流水线。每段内一次运行是**三阶段**：构建器为目标解析调度器，调度器*准备*一个归一化的 `SamplerSet`（读取当前值、解析采样器、固定端点），随后解释器驱动一个*连续*采样循环，锚定到运行的时间轴，并把每次帧写入编组到宿主线程。本节画出运行生命周期、节拍与 UI 线程跳跃，以及错误路径 —— 全部用 PlantUML 时序图。

## 子页

- [运行生命周期](00_运行生命周期/index.md) —— `Execute` → 调度器 → `Awake` → `Prepare` → 解释器，以及**准备好的状态**（每条声明路径一个 `SamplerSet` 条目）包含什么。
- [节拍与编组](01_节拍与编组/index.md) —— 循环如何决定*何时*采样（时间轴 + `FramePacerCore` / `ReusableTimerWait`），以及每一帧如何编组到所属线程。
- [错误路径](02_错误路径/index.md) —— 回调、采样器、宿主派发或 `Prepare` 抛异常时发生什么：`Warn` / `Error` 通道，以及为什么运行仍沿 `Canceled` + `Finally` 收尾。

## 流程摘要

| 场景 | 行为 |
|---|---|
| 正常运行 | `CoreExecute` 依次处理每个链段，每段：`await delay` → 调度器 `Execute`（门）→ 宿主线程上的 `Awake` → `Prepare` 为每个属性建一个 `SamplerSet` 条目 → 解释器连续采样并经宿主施加每帧 → `Completed` + `Finally`。 |
| `IsAutoReverse` | 正向趟之后解释器跑一个反向趟（同一组采样器；趟终点 `easedT = 0`）。 |
| `LoopTime` / `Repeat` | `LoopTime` 重复一个段的趟；`Repeat(count)` 重复一个段的*循环*，包裹从首段到该段的链，并重放首次迭代准备的帧集。 |
| 采样节奏 | 由时间轴决定*一帧何时是*；`1000 / max(1, FPS)` 毫秒只限制循环多久看一次。停泊的时间轴让循环零唤醒。 |
| `Pause` / `Resume` / `SetRate` / `Seek` | `Transition.*` 作用于运行的 `ITimeSourceControl`，**不是**调度器：暂停冻结时钟（暂停时间被扣除而非跳过），变速先重定基准（因此不跳位置），定位替换 `run.PassAnchor`（以及 `cycle` 重载下的趟计数器）。 |
| 共享时间轴 | 两个给定同一 `ITimeSourceControl` 的运行共享传输但保留各自的趟与位置，因此一次 `Pause` 冻结两者而一次 `Exit` 只停止一个。 |
| 索引实参 | 默认每帧重新求值，因此路径跟随它们，而终值留在首次读取的位置。`PathIndex.Frozen(i)` 在整个动画内钉住槽位，且是路径身份的一部分。 |
| 反射路径 | `TransitionProperty.FromProperty` 对每个 `PropertyInfo` 返回记忆化的共享路径，因此主题切换不再每次为每个目标重编译 getter/setter。 |
| 同一目标上的新互斥运行 | `CoreExecute` 先排空并取消上一运行的 token（递增代际）；上一运行在下一个检查点放弃，因此已排队的帧被跳过。 |
| `TransitionEventArgs.Handled = true` | 事件处理器让解释器抛 `OperationCanceledException` → `Canceled` + `Finally`；时间轴停止。 |
| 抛异常的回调 / 采样器 / 宿主 | 经 `Error` 上报一次，随后运行沿**正常**取消路径收尾，因此 `Canceled` 与 `Finally` 仍触发、循环资源仍释放。 |
| 无采样器 / 无效路径 | 不匹配目标运行时类型的路径在 `Prepare` 中被跳过（`UnreadablePath`）并经 `Warn` 上报；声明了却无采样器的**引用类型**路径被 `Execute` 拒绝（`TransitionPathUnsampleableException`），而不是什么都不动画。其他属性继续动画。 |
| 应用关闭 | `SamplerSet.CanSetValue()` 返回 `host.IsAlive == false` → `Apply` 跳过写入且不再触发事件。 |

相关分析：[设计模式 — 过渡动画](../../02_设计模式/03_过渡动画/index.md) · [复杂度 — 过渡动画](../../04_复杂度/03_过渡动画/index.md)
