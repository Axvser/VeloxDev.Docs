# 过渡动画 — 分段与循环

## 1. 时序、FPS 与循环语义

一个 `TransitionEffect` 驱动一个分段。它的时序成员（来自 `TransitionEffectCore`）：

- `Duration` —— 一趟的墙钟时长。`Duration = TimeSpan.Zero` 直接跳到终点（`TransitionEffects.Empty` 就把对象瞬时重置）。
- `FPS` —— *最大*采样率（默认 `60`）。解释器的让出间隔是 `1000 / FPS` 毫秒，但已流逝时间来自该趟的时间轴，所以 `FPS` 是上限而不是帧栅格。
- `IsAutoReverse` —— 正向趟之后，把同一趟反向播放。
- `LoopTime` —— 首趟之后*额外*的循环数。引擎播放 `0..LoopTime` 这些循环，即 `LoopTime + 1` 个正向趟（设了 `IsAutoReverse` 时每趟之后跟一趟反向）。演示用 `LoopTime: 2` + `IsAutoReverse: true` 得到三趟来回。`LoopTime = int.MaxValue` 表示**永久循环**。
- `Ease` —— `IEaseCalculator`，默认 `Eases.Default`。

**预期结果：** 一个 2 秒的 `LoopTime: 2` + `IsAutoReverse: true` 效果跑三趟正向、三趟反向，随后触发 `Completed`。

## 2. 把分段串成一条时间轴

用三个流式调用串起更多分段（每个分段有自己的 state + effect）：

- `.Await(timeSpan)` —— 在播放**本**分段前等待（作为第一个调用可推迟整条动画）。
- `.Then()` —— 在本分段之后立即开始下一段。
- `.AwaitThen(timeSpan)` —— 等待 `timeSpan`，随后开始下一段。

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.RenderTransform,
        [new TranslateTransform(200, 0), new ScaleTransform(1.3, 1.3)])
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        IsAutoReverse = true,
        FPS = 144,
        Ease = Eases.Circ.InOut,
        LoopTime = 2,
    })
    .AwaitThen(TimeSpan.FromSeconds(5))   // 等 5 秒，然后第二段
    .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        Ease = Eases.Sine.In,
    });
```

这是 WPF 演示的 `Animation2`。执行时解释器按顺序走链上的分段、遵守每一段的前置延时，因此整条链作为一条时间轴播放。前置等待按**墙钟**计量、每次醒来后重新求值，所以暂停期间流逝的那部分延时不会被消耗。

**预期结果：** 第一段用 2 秒移动并缩放该矩形（144 FPS 上限、圆形缓动、三趟来回）；随后停顿 5 秒；然后第二段以 `Eases.Sine.In` 淡入填充色。

## 3. 重复整条链 —— `Repeat(n)`

`LoopTime` 重复一个分段的**趟**；`Repeat(count)` 重复一个分段的**循环**，而循环包裹从首段到本段的链。`0` —— 默认 —— 跑一次，`int.MaxValue` 永远跑。

```csharp
Transition<Rectangle>.Create()
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .AwaitThen(TimeSpan.FromMilliseconds(250))
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(new TransitionEffect { Duration = TimeSpan.FromMilliseconds(500) })
    .Repeat(2);            // 整条两段链，跑三遍
```

循环**按结束位置嵌套**：三段各带 `Repeat(1)` 的链跑 `1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 1, 2, 3`。因此只有**末段**上的计数才重复整条链。

两个值得知道的后果：

- 重复的一段重放它**首次**迭代准备的那套帧集，而不重新读取目标。否则终点不同于起点的链会倒退，而某段写着更早分段都没碰过的属性时会一趟比一趟漂。
- 重放时 **`Awake` 不再触发**。`Start`、`Update`、`LateUpdate`、`Completed` 与诊断完全照常触发，因此一次重放与一趟一样可观测。

**预期结果：** 两段播放，随后再重复两遍，然后该趟完成 —— 迭代之间没有任何漂移。

## 4. 预设与效果事件

`TransitionEffects` 提供适配器 `TransitionEffect` 的三个可变预设：`Empty`（零时长 —— 瞬时跳转）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。执行前在副本上覆盖任意属性 —— 演示用 `Empty` 播放一份已声明的状态列表来重置对象：

```csharp
// 初始状态，显式声明（见「显式声明状态」）：
private static readonly Transition<Rectangle> Reset =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 1d)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Cyan));

// ……稍后瞬时恢复：
Reset.Effect(TransitionEffects.Empty).Execute(rect);
```

没有捕获步骤，所以重置列表是源码的一部分，必须与该动画自身声明的目标保持一致。

一个 effect 会触发生命周期事件（都是 `EventHandler<TransitionEventArgs>`；连同其基类 `TimeLineEventArgs`，该实参携带 `Handled` —— 置 `true` 可停止当前趟 —— 以及该帧的 `DeltaTime` / `TotalTime`，而 `Loop` / `Cycle` 说明运行到了哪里）：

- `Awaked` —— 一次，在调度器开始时（值归一化之前）。
- `Start` —— 每次解释器运行一次，在采样循环开始时。
- `Update` —— 每帧写入值之前；`LateUpdate` —— 其后立刻。
- `Completed` —— 最后一趟正常结束后。
- `Canceled` —— 被打断时（新的互斥动画、`Transition.Exit`，或 `Handled = true`）。
- `Finally` —— 在*任意*结束路径上总是触发，在 `Completed` 或 `Canceled` 之后。

另有两个事件报告**诊断**而非生命周期。每个 `stage` 每次运行至多报一次，因此逐帧发生的情况不会刷屏：

```csharp
var effect = new TransitionEffect
{
    Duration = TimeSpan.FromSeconds(1),
    Ease = Eases.Sine.InOut,
};
effect.Start += (_, _) => Console.WriteLine("start");
effect.Completed += (_, _) => Console.WriteLine("completed");
effect.Canceled += (_, _) => Console.WriteLine("canceled");
effect.Finally += (_, _) => Console.WriteLine("finally");
effect.Warn += (_, e) => Console.WriteLine($"降级 @{e.Stage}：{e.Value}");   // 某帧被丢弃、某路径被跳过、属性无采样器
effect.Error += (_, e) => Console.WriteLine($"失败 @{e.Stage}：{e.Value}");  // 回调 / 采样器 / 宿主抛异常
```

**预期结果：** 干净的一趟先打印 `start`，随后 `completed` 再 `finally`；打断它则打印 `start`、`canceled`、`finally`；一条声明路径与目标运行时类型不符的运行会打印一行 `degraded @Unreadable` 然后继续。生命周期处理器由 `WeakDelegate` 承载，因此持有 effect 不会泄漏目标。

下一步：[执行与控制](../05_执行与控制/index.md) 说明一次过渡（或一条链）实际如何被启动、取消与操纵。
