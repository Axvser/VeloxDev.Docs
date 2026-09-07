# Transition — 执行与控制

## 1. 启动一个快照（一次性）

调用快照的 `Execute` 扩展（命名空间 `VeloxDev.TransitionSystem`）。执行立即返回，并在后台驱动帧循环：

```csharp
using VeloxDev.TransitionSystem;

Animation0.Execute(rect);                  // 互斥（默认）：CanMutualTask: true
Animation0.Execute(rect, CanMutualTask: false); // 与其它动画并发运行
Transition<Rectangle>.Execute(rect, Animation0); // 静态替代写法
```

`Execute` 作用于 *UI 绑定*目标时，既可在 UI 线程调用，也可在后台线程调用 —— 各框架的 `UIThreadInspector` 会从目标推导其所属 UI 线程，并编组每一帧写入（见 [UI线程与编组](../06_UI线程与编组/index.md)）。示例两种入口都演练了，例如 WPF 示例分别在 UI 线程直接调用 `Animation0.Execute(Rec0)`，以及在 `Task.Run(...)` 内调用同一动画。

**预期结果：** 记录的属性按效果的时长/缓动从当前值插值到目标值。调用在动画完成前就返回了。

## 2. 互斥 vs 并行

一个目标有且仅有一个**互斥**调度器：当 `CanMutualTask: true` 的动画运行时，在同一个目标上再启动另一个动画会**先取消**正在运行的那个（新运行前会调用 `scheduler.Exit()`）。这正是示例「重复」按钮每次点击都能干净地重启动画的原因。

要在同一目标上并行跑多个动画，传 `CanMutualTask: false`。每个并行运行各有自己的调度器，引擎会跟踪它们，以便稍后的 `Exit` 能统一停止：

```csharp
Animation0.Execute(rect, CanMutualTask: false);
Animation1.Execute(rect, CanMutualTask: false);   // 两者并发
```

**预期结果：** `CanMutualTask: false` 时两者互不取消，各自朝自己的目标前进。

## 3. 就地停止 —— `Transition.Exit`

`Transition.Exit(target)` 取消目标正在运行的动画，让属性停留在当前位置（*不会*跳到快照终点）。两个标志决定停哪些调度器：

- `IncludeMutual: true` —— 唯一的互斥调度器（默认行为）。
- `IncludeNoMutual: true` —— 所有并行（`CanMutualTask: false`）调度器。

```csharp
Transition.Exit(rect);                                   // 仅互斥
Transition.Exit(rect, IncludeMutual: true, IncludeNoMutual: true); // 全部停止
```

**预期结果：** 动画就地冻结。之后对同一目标再 `Execute` 会从冻结值重新开始。

## 4. 按目标调度器

每次 `Execute` 都通过 `TransitionSchedulerCore<...>.FindOrCreate(target, CanMutualTask)` 为目标解析一个调度器。互斥调度器按目标缓存在 `ConditionalWeakTable` 中（随目标一起消亡）；非互斥调度器每次运行新建，并在效果的 `Finally` 触发时释放。调度器用 `SemaphoreSlim` 串行化访问、持有该动画的 `CancellationTokenSource`，并把准备好的 `SamplerSet` 交给插值器/解释器。通常你无需碰它；需要时可用静态查找辅助函数直接寻址：

```csharp
using VeloxDev.TransitionSystem.Abstractions;   // TransitionSchedulerCore

if (TransitionSchedulerCore.TryGetMutualScheduler(rect, out var mutual))
{
    mutual.Exit();   // 取消正在运行的互斥动画
}
```

**预期结果：** 动画启动后查询目标返回其存活调度器；对其调用 `Exit()` 会取消当前运行（等价于 `Transition.Exit(rect)`）。
