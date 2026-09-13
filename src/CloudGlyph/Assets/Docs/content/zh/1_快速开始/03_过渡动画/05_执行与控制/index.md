# Transition — 执行与控制

## 1. 启动一次动画（一次性）

调用 `Transition<T>` 上的 `Execute(target, CanMutualTask)` **实例方法**（继承自 `StateSnapshotCore<T>`；命名空间 `VeloxDev.TransitionSystem`）。执行立即返回，并在后台驱动帧循环：

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                  // 互斥（默认）：CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false);         // 与其它动画并发运行
Transition<Rectangle>.Execute(rect, [Animation0]);      // 批量静态入口，默认 CanMutualTask: false
```

`Execute` 作用于 *UI 绑定*目标时，既可在 UI 线程调用，也可在后台线程调用 —— 各框架的 `UIThreadInspector` 会从目标推导其所属 UI 线程，并编组每一帧写入（见 [UI线程与编组](../06_UI线程与编组/index.md)）。示例两种入口都演练了，例如 WPF 示例分别在 UI 线程直接调用 `Animation0.Execute(Rec0)`，以及在 `Task.Run(...)` 内调用同一动画。

**预期结果：** 声明的属性按效果的时长/缓动从当前值插值到目标值。调用在动画完成前就返回了。

## 2. 互斥 vs 并行

一个目标有且仅有一个**互斥**调度器：当 `CanMutualTask: true` 的动画运行时，在同一个目标上再启动另一个动画会**先取消**正在运行的那个（新运行前会调用 `scheduler.Exit()`）。这正是示例「重复」按钮每次点击都能干净地重启动画的原因。

要在同一目标上并行跑多个动画，传 `CanMutualTask: false`。每个并行运行各有自己的调度器，引擎会跟踪它们，以便稍后的 `Exit` 能统一停止：

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // 两者并发
```

**预期结果：** `CanMutualTask: false` 时两者互不取消，各自朝自己的目标前进。

## 3. 就地停止 —— `Transition.Exit`

`Transition.Exit(target)` 取消目标正在运行的动画，让属性停留在当前位置（*不会*跳到声明的终点）。两个标志决定停哪些调度器：

- `IncludeMutual: true` —— 唯一的互斥调度器（默认行为）。
- `IncludeNoMutual: true` —— 所有并行（`CanMutualTask: false`）调度器。

```csharp
Transition.Exit(rect);                                   // 仅互斥
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // 全部停止
```

**预期结果：** 动画就地冻结。之后对同一目标再 `Execute` 会从冻结值重新开始。

## 4. 操控运行中的动画

`Exit` 让动画停下；传输接口的其余部分让它**继续动**。它们都是 `Transition` 上的静态方法、按目标寻址，并和 `Exit` 一样用两个标志选择要触及的调度器。

| 调用 | 作用 |
|---|---|
| `Transition.Pause(target)` | 就地冻结 |
| `Transition.Resume(target)` | 继续播放，按上次设置的速率 |
| `Transition.SetRate(target, 0.5)` | 速度减半且**不移动位置**；`0` 等于暂停 |
| `Transition.Seek(target, TimeSpan)` | 跳到当前这一程内的某处，速率不变 |
| `Transition.Seek(target, cycle, TimeSpan)` | 跳到编号为 `cycle` 的那一程 |
| `Transition.Position(target)` | 当前这一程走了多远 —— `TimeSpan` |
| `Transition.Cycle(target)` | 正在播放第几程 —— `int` |
| `Transition.IsPaused(target)` | 该目标上的动画是否**全部**处于暂停 |
| `Transition.Rate(target)` | 当前设置的速率 |

```csharp
Transition.Pause(rect);
Transition.SetRate(rect, 0.5);          // 暂停期间的设置会被记住，Resume 时生效
Transition.Seek(rect, TimeSpan.FromMilliseconds(300));
Transition.Resume(rect);
```

契约中六条调用者立刻会碰到的性质：

- **暂停是从动画里扣除，而不是跳过。** 时钟停止累加，所以暂停多久都不改变剩余时长 —— 而且暂停中的动画**不产生任何定时器唤醒**：它的采样循环停在信号上。
- **`SetRate` 不移动位置。** 时间轴先重设基准再改速率，所以播放中改速率是无缝的。暂停期间设置的速率会被记住，`Resume` 时生效。
- **时间只向前走。** 没有反向播放：负速率会被**拒绝**（`ArgumentOutOfRangeException`），而不是钳制。要回到某一点，用 `Seek`。
- **Seek 越过一程的终点就是把它跑完**，精确落在终点，而不是被钳制；负位置会被钉在该程的起点。
- **一程是有编号的，不只是时间。** 按 `cycle` 的 `Seek` 之所以存在，是因为绝对时间轴无法用时间点命名一程 —— 零时长的一程根本不消耗时间。跳过效果允许的最后一程，动画即结束，与自然跑完一致。
- **暂停中 Seek 只画出新位置，不会恢复播放。**

三个读取方法在**没有动画运行**时给出确定的答案而不是抛异常：`Cycle` 为 `0`、`Position` 为 `TimeSpan.Zero`、`Rate` 为 `0`、`IsPaused` 为 `false`。

```csharp
// demo 的「下一程」按钮
Transition.Seek(rect, Transition.Cycle(rect, IncludeMutual: true, IncludeNoMutual: true) + 1,
    TimeSpan.Zero, IncludeMutual: true, IncludeNoMutual: true);
```

**预期结果：** 读数（`paused` / `rate` / `pos` / `cycle`）跟随你下的指令变化，且处于上述任一状态时 `Exit` 依然能停下这场动画。

*验证依据：* `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` —— 控制面板以实时读数驱动 `Pause` / `Resume` / `SetRate` / `Seek`；WinUI、MAUI、Jalium、Avalonia、Blazor、WinForms 各 demo 走的是同一套接口。

## 5. 按目标调度器

每次 `Execute` 都通过 `TransitionSchedulerCore<...>.FindOrCreate(target, CanMutualTask)` 为目标解析一个调度器。互斥调度器按目标缓存在 `ConditionalWeakTable` 中（随目标一起消亡）；非互斥调度器每次运行新建，并在**整场动画**结束时才释放（完成后或被取消时），而不是某一程效果 `Finally` 触发时 —— 分段之间动画会停在 `Await` 间隙里，此时 `Exit()` 仍必须能找到并取消它。调度器用 `SemaphoreSlim` 串行化访问、持有该动画的 `CancellationTokenSource`，并把准备好的 `SamplerSet` 交给插值器/解释器。通常你无需碰它；需要时可用静态查找辅助函数直接寻址：

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // 取消正在运行的互斥动画
}
```

**预期结果：** 动画启动后查询目标返回其存活调度器；对其调用 `Exit()` 会取消当前运行（等价于 `Transition.Exit(rect)`）。

### 适配器那一半：`InterpolatorCore.CreateScheduler`

调度器的**类型实参** —— 检查器、解释器、调度优先级 —— 因平台而异。`Transition<T>` 是一个封闭的 `TransitionCore<...>`，其最后三个类型实参恰好就是它们，所以 `Transition<T>.Execute` 无需问谁就能点名。只把目标当作 `object` 知道的调用方做不到，于是适配器把同一套解析暴露为插值器上的虚方法：

```csharp
namespace VeloxDev.TransitionSystem.Abstractions;

public abstract class InterpolatorCore
{
    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect) => null;
}
```

主题系统（[动态主题](../../04_动态主题/index.md)）正是需要它的调用方 —— 它要在运行时类型各不相同的一批目标上驱动同一次切换，所以要问插值器该用哪个调度器来动画某个目标。`Transition<T>.Execute` 不走这条缝，因为 `T` 已经点名了那些类型实参。契约里有三点：

- **七个适配器都重写了它**（各自的 `PlatformAdapters/Interpolator.cs`），各自给出自己的 `UIThreadInspector` / `TransitionInterpreter` / 优先级三元组 —— WPF、Avalonia 与 Jalium 用 `DispatcherPriority`，WinUI 用 `DispatcherQueuePriority`，MAUI、WinForms 与 Razor 用 `NonPriority`。
- **`null` 是诚实的答案**，既表示「该平台没有接入这条缝」，也表示「该效果不属于该平台」（重写里会转换效果类型，因此答案与调度器自身运行前做的转换一致）。调用方随后做一次不带动画的切换，而不是启动一场画不出东西的动画。
- **实现必须走 `TransitionSchedulerCore<...>.FindOrCreate`，绝不能 `new`** —— 只有这条路径会把调度器登记在目标名下，这正是稍后一次 `Transition.Pause` / `Seek` / `Exit` 能找到该动画的原因。

作为快速入门的读者，你通常什么都不用写：适配器包已经实现了它。只有在你自己写适配器，或某次主题切换不动画时，才会遇到它。
