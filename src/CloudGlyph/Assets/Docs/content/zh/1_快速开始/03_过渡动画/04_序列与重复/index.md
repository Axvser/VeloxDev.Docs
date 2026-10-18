# 过渡动画 — 序列与重复

## 1. 时间、FPS 与循环语义

一个 `TransitionEffect` 驱动一个段。它的时间成员（来自 `TransitionEffectCore`）：

- `Duration` —— 一趟的墙钟长度。`Duration = TimeSpan.Zero` 直接跳到终点（`TransitionEffects.Empty` 就是这样瞬间重置对象）。
- `FPS` —— **最大**采样率（默认 `60`）。解释器的让出间隔是 `1000 / FPS` 毫秒，但经过的时间来自运行的时间轴，因此 `FPS` 是上限，不是帧栅格。
- `IsAutoReverse` —— 正向趟之后，把同一趟倒放。
- `LoopTime` —— 首趟之后的*额外*循环数。引擎播放 `0..LoopTime` 趟，即 `LoopTime + 1` 个正向趟（设置 `IsAutoReverse` 时每趟后跟一个反向趟）。demo 用 `LoopTime: 2` + `IsAutoReverse: true` 做三次来回。`LoopTime = int.MaxValue` 表示**永远循环**。
- `Ease` —— `IEaseCalculator`，默认 `Eases.Default`。

**预期结果：** 一个 2 秒、`LoopTime: 2` + `IsAutoReverse: true` 的效果跑三个正向趟与三个反向趟，然后触发 `Completed`。

## 2. 把多个段串成时间轴

用三个流式调用追加段（每段有自己的 state + effect）：

- `.Await(timeSpan)` —— 在播放**本段**之前等待（作为第一个调用时用于延迟整个动画）。
- `.Then()` —— 本段结束后立即开始下一段。
- `.AwaitThen(timeSpan)` —— 等待 `timeSpan`，然后开始下一段。

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
    .AwaitThen(TimeSpan.FromSeconds(5))   // wait 5 s, then the second segment
    .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        Ease = Eases.Sine.In,
    });
```

这是 WPF demo 的 `Animation2`。执行时，解释器按顺序遍历链接的段，并遵守每段的引入延迟，因此整条链作为一条时间轴播放。引入等待按**墙钟**计量，并在每次唤醒后重新求值，因此暂停期间流逝的那部分延迟不会被消耗。

**预期结果：** 第一段移动并缩放矩形 2 秒（144 FPS 上限、圆形缓动、三次来回）；随后停顿 5 秒；第二段用 `Eases.Sine.In` 把填充色渐入黄色。

## 3. 重复一条链 —— `Repeat(n)`

`LoopTime` 重复一个段的**趟**；`Repeat(count)` 重复一个段的**循环**，它包裹从首段到本段的链。`0` —— 默认 —— 跑一次，`int.MaxValue` 永远跑。

```csharp
Transition<Rectangle>.Create()
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .AwaitThen(TimeSpan.FromMilliseconds(250))
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(new TransitionEffect { Duration = TimeSpan.FromMilliseconds(500) })
    .Repeat(2);            // the whole two-segment chain, three times over
```

循环**按结束位置嵌套**：三个各带 `Repeat(1)` 的段按 `1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 1, 2, 3` 运行。因此只有**末段**上的计数才重复整条链。

两个值得知道的后果：

- 重复段重放它**首次**迭代准备的帧集，而不是重新读取目标。否则端点不同于起点的链会倒退，而某段写着更早分段都没碰过的属性时会一趟比一趟漂。
- `Awake` 在重放时**不**再触发。`Start`、`Update`、`LateUpdate`、`Completed` 与诊断照常触发，因此重放和普通趟一样可观察。

**预期结果：** 两段播放，然后再重复两次，随后运行完成 —— 迭代之间没有漂移。

## 4. 预设与效果事件

`TransitionEffects` 提供三个可变的适配器 `TransitionEffect` 预设：`Empty`（零时长 —— 瞬间跳转）、`Theme`（0.46 秒）与 `Hover`（0.32 秒）。执行前可在副本上覆盖任意属性 —— demo 通过在 `Empty` 下播放声明状态列表来重置对象：

```csharp
// The initial state, declared explicitly (see "Declare State Explicitly"):
private static readonly Transition<Rectangle> Reset =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 1d)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Cyan));

// ... later, restore it instantly:
Reset.Effect(TransitionEffects.Empty).Execute(rect);
```

没有捕获步骤，因此重置列表是源码的一部分，必须与动画自己声明的目标保持同步。

一个效果会抛出生命周期事件（都是 `EventHandler<TransitionEventArgs>`；配合基类 `TimeLineEventArgs`，该实参携带 `Handled` —— 置 `true` 可停止当前趟 —— 以及该帧的 `DeltaTime` / `TotalTime`，而 `Loop` / `Cycle` 说明运行到了哪里）：

- `Awaked` —— 调度器开始时一次（在值归一化之前）。
- `Start` —— 每次解释器运行一次，采样循环开始时。
- `Update` —— 每帧写入值之前；`LateUpdate` —— 紧随其后。
- `Completed` —— 最后一趟正常结束后。
- `Canceled` —— 被中断时（新的互斥动画、`Transition.Exit`，或 `Handled = true`）。
- `Finally` —— 在**任何**结束路径上总会触发，在 `Completed` 或 `Canceled` 之后。

另外两个事件报告的是**诊断**而非生命周期。每个 `stage` 每次运行至多上报一次，因此逐帧条件不会刷屏：

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
effect.Warn += (_, e) => Console.WriteLine($"degraded @{e.Stage}: {e.Value}");   // dropped frame, skipped path, unsampled property
effect.Error += (_, e) => Console.WriteLine($"failed @{e.Stage}: {e.Value}");   // a throwing callback / sampler / host
```

**预期结果：** 一次干净运行打印 `start`，然后 `completed`、`finally`；中断它则打印 `start`、`canceled`、`finally`；一条声明的路径与目标运行时类型不符时打印一行 `degraded @Unreadable` 并继续。生命周期处理器由 `WeakDelegate` 支撑，因此持有 effect 不会泄漏目标。

下一步：[执行与控制](../05_执行与控制/index.md) 说明一次过渡（或链）如何真正启动、取消与操纵。
