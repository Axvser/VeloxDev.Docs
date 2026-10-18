# 过渡动画 — 执行与控制

## 1. 启动一次过渡（一次性）

调用过渡的 `Execute(target, CanMutualTask)` 实例方法（继承自 `StateSnapshotCore<T>`，命名空间 `VeloxDev.TransitionSystem.Abstractions`）。执行立即返回，并在后台驱动帧循环：

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                       // mutual-exclusive (default): CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false); // run concurrently with other animations
```

还有一个静态批入口 —— `Transition<T>.Execute(T target, IEnumerable<Transition<T>> values, bool CanMutualTask = false)` —— 依次运行批中每个过渡；它在 `Transition.cs` 中经源码核实，但 demo 未使用。

对 *UI 绑定*目标的 `Execute` 可以从 UI 线程**或**后台线程调用 —— 适配器宿主从目标推导所属 UI 线程并编组每帧写入（见[UI线程与编组](../06_UI线程与编组/index.md)）。demo 两个入口都练过，例如 WPF demo 在 UI 线程上以及 `Task.Run(...)` 内用 `Animation0.Execute(Rec0)` 启动同一个动画。

**预期结果：** 已记录属性在效果的时长 / 缓动内从当前值插值到目标值。调用在动画结束前返回。

## 2. 互斥与并发

一个目标有一个**互斥**调度器：当 `CanMutualTask: true` 的动画在跑时，在同一目标上启动另一个动画会**先取消正在跑的那个**。这就是 demo 的「重复」按钮每次点击都能干净重启动画的原因。

要在同一目标上同时跑多个动画，传 `CanMutualTask: false`。每个并发运行有自己的调度器，引擎会跟踪它们，以便后续 `Exit` 能停止：

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // both run concurrently
```

关键可观察量是 `TransitionScheduler.TryGetNoMutualScheduler(target, out var schedulers)` —— 返回数组的**长度**就是仍注册着的并发运行数。相反，互斥表按目标缓存整个生命周期且从不清除，因此 `TryGetMutualScheduler` 返回 true 只意味着「这个目标跑过一次互斥动画」。

**预期结果：** 用 `CanMutualTask: false` 时两个动画互不取消，各自朝自己的目标推进。

## 3. 在多个动画之间共享一条时间轴

`Execute` 还有一个接收时间轴的重载：

```csharp
using VeloxDev.Timing;

ITimeSourceControl timeline = new TimeSourceCore();
Animation0.Execute(rect0, timeline);
Animation1.Execute(rect1, timeline);   // same transport
```

共享时间轴的动画共享一套传输：暂停、改变速率或定位**其中一个**会一起移动全部，而每个保留自己的趟与位置。这正是编舞式分组所需 —— 多个动画保持同步而彼此互不知晓。不传该重载时，每一趟都从 `TimerCore.CreateTimeSource<ITimeSourceControl>()` 得到自己的私有源。

**预期结果：** `Transition.Pause(rect0, IncludeMutual: true, IncludeNoMutual: true)` 冻结*两个*矩形，因为两趟读同一个源。`Transition.Exit(rect0, ...)` 仍只停止 `rect0` —— 退出取消运行，不取消时钟。

## 4. 原地停止 —— `Transition.Exit`

`Transition.Exit(target)` 取消目标上正在跑的动画，并把属性留在当前位置（它*不会*跳到过渡的终值）。两个标志选择停止哪些调度器：

- `IncludeMutual: true` —— 单个互斥调度器（默认）。
- `IncludeNoMutual: true` —— 所有并发（`CanMutualTask: false`）调度器。

```csharp
Transition.Exit(rect);                                   // mutual only
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // stop everything
```

取消是一个**信号**：运行在下一个 await 处停止，因此 `Exit` 返回时它可能仍在释放调度器。对随后的一次互斥 `Execute` 来说没关系，后者会在调度器自己的门后、排在被取消的运行之后。

**预期结果：** 动画原地冻结（由 `AUTO TEST` 用例 `LoadModes_MatchTheLibrarySemantics` 的「停止全部把目标冻在原地」验证）。随后在同一目标上的 `Execute` 从冻结值重新开始。

## 5. 操纵正在运行的动画

`Exit` 停止运行；传输的其余部分在**保持其活着**的同时移动它。全部是 `Transition` 上的静态方法，按目标寻址，并接受与 `Exit` 相同的两个标志来选择要触达的调度器。

| 调用 | 效果 |
|---|---|
| `Transition.Pause(target)` | 原地冻结运行 |
| `Transition.Resume(target)` | 以最后一次设置的速率继续 |
| `Transition.SetRate(target, 0.5)` | 速度减半而不移动位置；`0` 速率冻结时钟但不暂停（`IsPaused` 仍为 false，`Resume` 也不会让它前进） |
| `Transition.Seek(target, TimeSpan)` | 跳到当前趟内的位置，保持速率 |
| `Transition.Seek(target, cycle, TimeSpan)` | 跳到编号 `cycle` 的那一趟 |
| `Transition.Position(target)` | 当前趟内已走多远 —— 一个 `TimeSpan` |
| `Transition.Cycle(target)` | 正在播放哪一趟 —— 一个 `int` |
| `Transition.IsPaused(target)` | 目标上**每一个**动画是否都已暂停 |
| `Transition.Rate(target)` | 它被设置的速率 |

```csharp
Transition.Pause(rect);
Transition.SetRate(rect, 0.5);          // remembered while paused, applied on Resume
Transition.Seek(rect, TimeSpan.FromMilliseconds(300));
Transition.Resume(rect);
```

契约的六条性质，调用方一用就会遇到：

- **暂停是从动画中扣除，不是跳过。** 时钟停止累积，因此任意长度的暂停都不改变剩余时长 —— 而且被暂停的动画**不消耗定时器唤醒**，因为它的采样循环停泊在一个信号上。
- **`SetRate` 不移动位置。** 时间轴在改速率之前先重定基准，因此播放中改变速率是无缝的。暂停时设置的速率会被记住，并在 `Resume` 时生效。
- **时间只向前走。** 没有反向播放：负速率会被**拒绝**并抛 `ArgumentOutOfRangeException`，而不是夹取。要回到某个点，用 `Seek`。
- **定位超过一趟的终点会结束该趟**，精确落在终点而不是被夹取；负位置钉在该趟起点。
- **一趟有编号，不只是时间。** 按 `cycle` 定位之所以存在，是因为绝对时间轴否则无法命名一趟 —— 零时长趟根本不消耗时间。跳过效果允许的最后一趟会结束动画，和跑出终点完全一样。
- **暂停时定位会画出新位置但不会恢复运行。**

三个查询在*无运行*时给出答案而不是抛异常：`Cycle` 给 `0`、`Position` 给 `TimeSpan.Zero`、`Rate` 给 `0`，`IsPaused` 给 `false`（共四个）。

```csharp
// the demo's "next pass" button
Transition.Seek(rect, Transition.Cycle(rect, IncludeMutual: true, IncludeNoMutual: true) + 1,
    TimeSpan.Zero, IncludeMutual: true, IncludeNoMutual: true);
```

**预期结果：** 读数（`paused` / `rate` / `pos` / `cycle`）跟随你的请求，且 `Exit` 从这些状态中任一都能停止运行。

*核实于：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` —— 它的控制面板在活动的 `IsPaused` / `Rate` / `Position` / `Cycle` 读数上驱动 `Pause` / `Resume` / `SetRate` / `Seek`。`AUTO TEST` 用例 `TimelineControl_SteersTheRunningAnimation` 在全部七个平台上断言同样行为：暂停冻结位置并保持冻结、恢复推进、四分之一速度在同样墙钟内明显走得更少、跳到另一趟会改变 `cycle`。

## 6. 按目标的调度器

每次 `Execute` 都通过 `TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>.FindOrCreate(target, CanMutualTask)` 为目标解析一个调度器：

| 种类 | 生命周期 | 后果 |
|---|---|---|
| 互斥 | 每个目标一个，缓存在 `ConditionalWeakTable` | 随目标一起消失 |
| 非互斥 | 每次运行一个，在**整个**动画期间注册 / 注销 —— 包括段之间的 `Await` 间隙 | 间隙中的 `Exit` 仍能找到并取消它 |

调度器经 `SemaphoreSlim` 串行化访问，跟踪动画的每个活动运行，并把准备好的 `SamplerSet<TPriorityCore>` 交给解释器。你通常从不直接碰它，但静态查找助手可以：

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // cancel the running mutual animation
}
```

调度器还携带链循环所依赖的两个成员：`ExecuteCapturing`（跑一个段并交回它准备的帧集）与 `Replay(frameSet, effect)`（用**同一组**端点再跑该段；目标不被重读，`Awake` 不再触发）。`Repeat` 是这对成员的唯一读者。

**预期结果：** 动画启动后查询目标会返回它的活动调度器；对其调用 `Exit()` 取消当前运行（等价于 `Transition.Exit(rect)`）。

## 7. 适配器那一半：`InterpolatorCore.CreateScheduler`

调度器的*类型实参* —— 宿主、解释器、调度器优先级 —— 按平台固定。`Transition<T>` 是封闭的 `TransitionCore<...>`，其最后三个类型实参正是这些，因此 `Transition<T>.Execute` 无需询问任何人就能命名它们。只把目标当作 `object` 的调用方做不到，因此适配器在它的 interpolator 上以虚方法暴露同样的解析：

```csharp
namespace VeloxDev.TransitionSystem.Abstractions;

public abstract class InterpolatorCore
{
    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect) => null;
}
```

主题系统（[动态主题](../../../2_API/04_动态主题/index.md)）就是需要它的调用方：它跨许多运行时类型的目标驱动一次切换，因此向 interpolator 询问用哪个调度器动画某个目标。`Transition<T>.Execute` 不走它 —— `T` 已经命名了类型实参。契约带有三点：

- **每个适配器都重写它**（`PlatformAdapters/Interpolator.cs`），各自用宿主 / `TransitionInterpreter` / 优先级三元组作答 —— WPF、Avalonia 与 Jalium 用 `DispatcherPriority`；WinUI 用 `DispatcherQueuePriority`；MAUI、WinForms 与 Razor 用 `NonPriority`。
- **`null` 是诚实的答案**，既表示「此平台未接入」，也表示「该 effect 不属于此平台」（重写会转换 effect，因此答案镜像调度器运行前自己的转换）。调用方随后无动画地切换，而不是启动一次画不出东西的运行。
- **实现必须走 `TransitionSchedulerCore<...>.FindOrCreate`，绝不能 `new`** —— 只有那条路径会把调度器归档到目标名下，这正是后续 `Transition.Pause` / `Seek` / `Exit` 能找到动画的原因。

作为 QuickStart 读者，你通常什么都不用写：适配器包已经实现了它。只有自己写适配器，或主题切换不动画时，你才会遇到它。
