# Transition — 分段与循环

## 1. 时序、FPS 与循环语义

一个 `TransitionEffect` 驱动一个分段。其时序成员（来自 `TransitionEffectCore`）：

- `Duration` —— 单程的墙钟时长。`Duration = TimeSpan.Zero` 会直接跳到终点（这正是 `TransitionEffects.Empty` 让对象瞬时重置的方式）。
- `FPS` —— *最大*采样率（默认 `60`）。解释器的让步间隔是 `1000 / FPS` 毫秒，但流逝时间来自 `Stopwatch`，所以 `FPS` 是上限而非帧网格。
- `IsAutoReverse` —— 正向程结束后，把同一程反向再放一遍。
- `LoopTime` —— 在首程之后的*额外*循环次数。引擎执行 `0..LoopTime` 各周期，即 `LoopTime + 1` 次正向程（开启 `IsAutoReverse` 时每程再跟一次反向程）。示例用 `LoopTime: 2` + `IsAutoReverse: true` 播放三个来回。`LoopTime = int.MaxValue` 表示**无限循环**。
- `Ease` —— `IEaseCalculator`，默认 `Eases.Default`。

**预期结果：** 一个 2 秒的 `LoopTime: 2` + `IsAutoReverse: true` 效果执行三次正向程与三次反向程，然后触发 `Completed`。

## 2. 把分段链成时间线

用三个流式调用串联更多分段（每段有自己的状态 + 效果）：

- `.Await(timeSpan)` —— 先等待，再播放**当前**段（作为首调用可让整个动画延迟开始）。
- `.Then()` —— 本段结束后立即开始下一段。
- `.AwaitThen(timeSpan)` —— 等待 `timeSpan` 后开始下一段。

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
    .AwaitThen(TimeSpan.FromSeconds(5))   // 等 5 秒，再进入第二段
    .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(2),
        Ease = Eases.Sine.In,
    });
```

这是 WPF 示例中的 `Animation2`。执行时，解释器按顺序走完链表中的各段，尊重每段的引导延迟（每段前都会先出队 `spans`），于是整条链作为一条时间线播放。

**预期结果：** 第一段在 2 秒内移动并缩放矩形（144 FPS 上限、圆形缓动、三个来回）；随后暂停 5 秒；第二段用 `Eases.Sine.In` 淡入填充色。

## 3. 预设与效果事件

`TransitionEffects` 提供三个可变的适配器 `TransitionEffect` 预设：`Empty`（零时长 —— 瞬时跳变）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。执行前可在副本上覆盖任意属性 —— 示例用一个零时长效果把各初始值逐条写回来重置对象：

```csharp
private static Transition<Rectangle> CreateReset()
{
    return Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 1d)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Cyan))
        .Effect(TransitionEffects.Empty);   // Duration = 0 → 瞬时写回
}

// 需要时执行：
CreateReset().Execute(rect);
```

效果会触发生命周期事件（都是 `EventHandler<TransitionEventArgs>`；`TransitionEventArgs` 带 `Handled` —— 置为 `true` 即可停止当前程）：

- `Awaked` —— 调度器开始且值归一化前，触发一次。
- `Start` —— 每次解释器运行、采样循环开始时触发。
- `Update` —— 每次写帧前；`LateUpdate` —— 紧随其后。
- `Completed` —— 最后一程正常结束后触发。
- `Canceled` —— 被打断时触发（新的互斥动画、`Transition.Exit` 或 `Handled = true`）。
- `Finally` —— 无论成功或取消，在**任何**结束路径上都会触发。（非互斥调度器的簿记由这次运行自身释放，不由该事件释放。）

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
```

**预期结果：** 正常运行时打印 `start`、`completed`、`finally`；打断时打印 `start`、`canceled`、`finally`。事件处理器由 `WeakDelegate` 支撑，因此持有效果不会泄漏目标。

下一步：[执行与控制](../05_执行与控制/index.md) 说明如何真正启动、取消与并行运行一个 `Transition<T>`（或链）。
