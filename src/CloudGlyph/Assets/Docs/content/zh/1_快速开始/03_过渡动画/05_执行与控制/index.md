# 过渡动画 — 执行与控制

## 1. 启动一次过渡（一次性）

调用过渡的 `Execute(target, CanMutualTask)` 实例方法（继承自 `StateSnapshotCore<T>`，命名空间 `VeloxDev.TransitionSystem.Abstractions`）。执行立即返回，帧循环在后台推进：

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                       // 互斥（默认）：CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false); // 与其他动画并发运行
```

还有一个静态批入口 `Transition<T>.Execute(T target, IEnumerable<Transition<T>> values, bool CanMutualTask = false)`，逐个运行批中的过渡；它在 `Transition.cs` 中经源码核验，但未被演示演练。

对 *UI 绑定* 目标调用 `Execute` 可以在 UI 线程**或**后台线程 —— 适配器宿主从目标推出所属 UI 线程并编组每一帧写入（见 [UI 线程与编组](../06_UI线程与编组/index.md)）。演示演练了两个入口，例如 WPF 演示在 UI 线程上用 `Animation0.Execute(Rec0)`、也在 `Task.Run(...)` 里启动同一条动画。

**预期结果：** 已记录的属性在效果的时长/缓动内从它们的当前值插值到目标值。调用在动画完成之前就返回。

## 2. 互斥 vs 并发

一个目标只有一个**互斥**调度器：当一条 `CanMutualTask: true` 的动画在跑时，在同目标上启动另一条动画会**先取消正在跑的那条**。这就是演示里「重复」按钮每次点击都能干净地重启动画的原因。

要在同一个目标上同时跑多条动画，传 `CanMutualTask: false`。每条并发运行有自己的调度器，引擎会跟踪它们，以便之后的 `Exit` 能停掉它们：

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // 两条同时跑
```

承重的可观测量是 `TransitionScheduler.TryGetNoMutualScheduler(target, out var schedulers)` —— 返回数组的**长度**即在册并发的运行数。互斥表相反：它按目标缓存一辈子、从不清理，所以 `TryGetMutualScheduler` 返回 true 只说明「这个目标跑过互斥动画」。

**预期结果：** 用 `CanMutualTask: false` 时两条动画互不取消，各自朝自己的目标推进。

## 3. 让多个动画共享一条时间轴

`Execute` 还有一个接收该趟锚定时间轴的重载：

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = new TimeSourceCore();
Animation0.Execute(rect0, timeline);
Animation1.Execute(rect1, timeline);   // 同一套传输
```

共享一条时间轴的动画共享一套传输：暂停、变速或定位**其中一条**会一起移动全部，而每条保留自己的趟与自己在该趟中的位置。这正是编舞式分组所需 —— 多个动画保持同步而彼此互不知晓。不用这个重载时，每一趟从 `TimerCore.CreateTimeSource<ITimeSourceControl>()` 得到自己的私有源。

**预期结果：** `Transition.Pause(rect0, IncludeMutual: true, IncludeNoMutual: true)` 会冻结*两个*矩形，因为两趟读的是同一个源。`Transition.Exit(rect0, ...)` 仍然只停 `rect0` —— 退出取消的是运行，不是时钟。

## 4. 原地停止 —— `Transition.Exit`

`Transition.Exit(target)` 取消目标上正在运行的动画，并把属性留在它当前所在处（*不*跳到过渡的终值）。两个标志选择停哪些调度器：

- `IncludeMutual: true` —— 那一个互斥调度器（默认）。
- `IncludeNoMutual: true` —— 全部并发（`CanMutualTask: false`）调度器。

```csharp
Transition.Exit(rect);                                   // 仅互斥
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // 全部停掉
```

取消是一个**信号**：该趟在下一个 await 处停下，因此 `Exit` 返回时它可能仍在释放调度器。对随后的一次互斥 `Execute` 没问题，它会在调度器自己的门后、排在被取消那趟之后。

**预期结果：** 动画原地冻结（由 `AUTO TEST` 用例 `LoadModes_MatchTheLibrarySemantics` 的「停止全部把目标冻在原地」核验）。随后在同目标上的 `Execute` 从冻结值重新开始。

## 5. 操纵一条正在运行的动画

`Exit` 停掉一趟；传输的其余部分**移动**一趟并让它活着。全部都在 `Transition` 上以静态形式、按目标寻址，并像 `Exit` 一样接收两个标志来选择够得着哪些调度器。

| 调用 | 效果 |
|---|---|
| `Transition.Pause(target)` | 把该趟冻结在原处 |
| `Transition.Resume(target)` | 以它最后设置的速率继续 |
| `Transition.SetRate(target, 0.5)` | 速度减半且不移动位置；`0` 速率冻结时钟但不暂停（`IsPaused` 仍为 false，`Resume` 也不会让它推进） |
| `Transition.Seek(target, TimeSpan)` | 跳到当前趟内的某个位置，保持速率 |
| `Transition.Seek(target, cycle, TimeSpan)` | 跳到编号为 `cycle` 的那一趟 |
| `Transition.Position(target)` | 进入当前趟多深 —— 一个 `TimeSpan` |
| `Transition.Cycle(target)` | 正在播第几趟 —— 一个 `int` |
| `Transition.IsPaused(target)` | 目标上的**每一个**动画是否都被暂停 |
| `Transition.Rate(target)` | 它被设成的速率 |

```csharp
Transition.Pause(rect);
Transition.SetRate(rect, 0.5);          // 暂停期间被记住，Resume 时生效
Transition.Seek(rect, TimeSpan.FromMilliseconds(300));
Transition.Resume(rect);
```

契约的六个性质，调用方一用上就会遇到：

- **暂停是被排除出动画的，不是被跳过的。** 时钟停止累积，因此任意长度的暂停都让剩余时长不变 —— 而暂停的动画**不耗定时器唤醒**，因为它的采样循环停在信号上。
- **`SetRate` 不移动位置。** 改速率之前时间轴先重基，所以播放中途改动是无缝的。暂停期间设的速率被记住，`Resume` 时生效。
- **时间只向前走。** 没有反向播放：负速率被 **拒绝**（`ArgumentOutOfRangeException`），而不是夹取。要回到某个点就 `Seek` 过去。
- **定位越过一趟末尾会结束它**，精确落在端点而不是被夹取；负位置被钉在该趟起点。
- **一趟有编号，不只是有时间。** 按 `cycle` 定位之所以存在，是因为绝对时间轴无法以别的方式指名一趟 —— 零时长的一趟根本不耗时间。跳过后效果允许的最后一趟会结束动画，和跑到终点完全一样。
- **暂停期间定位会画出新位置而不恢复播放。**

三个读取器对*无运行*给出答案而非抛异常：`Cycle` 给 `0`，`Position` 给 `TimeSpan.Zero`，`Rate` 给 `0`，`IsPaused` 给 `false`。

```csharp
// 演示里的「下一趟」按钮
Transition.Seek(rect, Transition.Cycle(rect, IncludeMutual: true, IncludeNoMutual: true) + 1,
    TimeSpan.Zero, IncludeMutual: true, IncludeNoMutual: true);
```

**预期结果：** 读数（`paused` / `rate` / `pos` / `cycle`）跟随你所要求的状态，且从这些状态里 `Exit` 仍然能停掉该趟。

*核验：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` —— 它的控制面板在活的 `IsPaused` / `Rate` / `Position` / `Cycle` 读数上驱动 `Pause` / `Resume` / `SetRate` / `Seek`。`AUTO TEST` 用例 `TimelineControl_SteersTheRunningAnimation` 在全部七个平台上断言同样的行为：暂停冻结位置并保持冻结、恢复让它推进、四分之一速率在同样墙钟里走得更少、跳到另一趟会移动 `cycle`。

## 6. 按目标调度器

每次 `Execute` 都经 `TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>.FindOrCreate(target, CanMutualTask)` 为目标解析一个调度器。互斥调度器按目标缓存在 `ConditionalWeakTable` 里（随目标回收）；非互斥调度器每次运行新建，并在**整条**动画期间登记/注销 —— 包括分段之间的 `Await` 间隔 —— 因此间隔期间的 `Exit` 仍能找得到并取消它们。调度器经 `SemaphoreSlim` 串行化访问，跟踪该动画的每一个活着的 run，并把准备好的 `SamplerSet<TPriorityCore>` 交给解释器。你通常永不触碰它，但需要时可以用静态查找助手直接寻址：

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // 取消正在跑的互斥动画
}
```

调度器还携带链的循环赖以建立的两个成员：`ExecuteCapturing`，跑一个分段并交还它准备的那套帧集；以及 `Replay(frameSet, effect)`，对**同一**端点再跑那一遍（目标不重读、`Awake` 不重触发）。`Repeat` 是这一对的唯一读者。

**预期结果：** 动画启动后查询该目标会返回它活着的调度器；对它 `Exit()` 会取消当前趟（等价于 `Transition.Exit(rect)`）。

## 7. 适配器那一半：`InterpolatorCore.CreateScheduler`

一个调度器的*类型实参* —— 宿主、解释器、调度器优先级 —— 按平台固定。`Transition<T>` 是一个封闭的 `TransitionCore<...>`，其最后三个类型实参正是那些，因此 `Transition<T>.Execute` 不必问谁就能命名它们。只把目标当作 `object` 的调用方做不到，于是适配器把同一套解析暴露为它插值器上的一个虚方法：

```csharp
namespace VeloxDev.TransitionSystem.Abstractions;

public abstract class InterpolatorCore
{
    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect) => null;
}
```

主题系统（[动态主题](../../04_动态主题/index.md)）正是需要它的调用方 —— 它一次切换横跨多种运行时类型的目标，于是问插值器该用哪个调度器给某个目标做动画。`Transition<T>.Execute` 不走它，因为 `T` 已经命名了那些类型实参。契约承载三点：

- **每个适配器都重写它**（`PlatformAdapters/Interpolator.cs`），各自用自己那套宿主 / `TransitionInterpreter` / 优先级三元组作答 —— WPF、Avalonia、Jalium 为 `DispatcherPriority`；WinUI 为 `DispatcherQueuePriority`；MAUI、WinForms、Razor 为 `NonPriority`。
- **`null` 是诚实答案**，对「本平台未接入」与「这个 effect 不属于本平台」都是（重写会强制转换 effect，因此答案镜像调度器自己运行前所做的强制转换）。调用方于是不带动画地完成切换，而不是启动一次什么都画不出来的运行。
- **实现必须走 `TransitionSchedulerCore<...>.FindOrCreate`，绝不 `new`** —— 只有那条路径把调度器登记在目标名下，那正是后来的 `Transition.Pause` / `Seek` / `Exit` 能找到该动画的原因。

作为快速开始的读者，你通常在这里什么都不写：适配器包已经实现了它。你会在自己写适配器时，或某个主题切换没有动画时遇到它。
