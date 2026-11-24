# 过渡动画

一条过渡是若干段组成的链，每段有一个效果和一组采样器。启动时扁平化链，并为每个被动画的属性准备一个采样项。此后代价按帧计：一次缓动求值、每个属性一次采样调用、一次宿主派发。若有 $t$ 条并发过渡、每条 $k$ 个属性，一帧花费 $O(t k)$——并且每条过渡拥有一个定时器，所以唤醒次数也与 $t$ 成正比。

记号：一条链 $s$ 段，第 $s$ 段 $k_s$ 个属性，活跃过渡 $t$，生命周期处理器 $h$，属性路径长度 $L$，基类深度 $D$，已注册采样器 $R$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| 扁平化链 | $O(s)$ | $O(s)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:417` |
| 准备采样器 | $O(\sum_s k_s (L + D))$ | $O(\sum_s k_s)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs:139` |
| 解析单个采样器 | 精确 $O(1)$，基类 $O(D)$，接口回退 $O(R)$ | — | `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs:51` |
| 一个采样帧 | 每条过渡 $O(k)$ | $O(1)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:313` |
| 全部活跃过渡，一帧 | $O(t k)$ + $O(t)$ 次派发 | — | `Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:355` |
| 重复 $n$ 次 | $n+1$ 轮，每轮新解释器 | 每轮 $O(k)$ | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:472` |
| 退出 / 暂停 / 设速率 | 该目标的 $O(r)$ | — | `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:30` |

## 启动对链线性

段通过遍历链收集，每收集一段就克隆效果：

```csharp
currentNode = root;
do {
    segments.Add((currentNode.interpolator, currentNode.delay, currentNode.effect.Clone(), currentNode.state));
    repeats.Add(currentNode.RepeatTime);
    currentNode = currentNode.next;
} while (currentNode is not null);
```

出处：`Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs:417-425`

准备阶段随后通过宿主读取每个属性一次并构建采样项。采样器解析常见情况是字典命中；基类遍历增加 $O(D)$，接口类型属性回退为扫描注册表 $O(R)$。

## 每帧循环

每个采样循环推进共享时间线，发出帧，然后等待下一个采样间隔：

```csharp
while (true)
{
    if (cts.IsCancellationRequested || Args.Handled) throw new OperationCanceledException();
    if (!timeline.IsAdvancing) { EmitFrame(...); await timeline.WaitWhileStalledAsync(cts.Token); continue; }
    var elapsedTicks = timeline.Ticks - run.PassAnchor;
    if (EmitFrame(...)) return;
    var sampleIntervalMs = 1000.0 / Math.Max(1, effect.FPS);
    await new FrameWait(this, TimeSpan.FromMilliseconds(sampleIntervalMs), cts.Token);
}
```

出处：`Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs:313-341`

`EmitFrame` 求值缓动一次，并在宿主线程应用采样器集：

```csharp
foreach (var entry in _entries)
{
    if (!CanSetValue()) return;
    try { entry.Sampler.InsertFrame(target, entry.Property, ref entry.Working, entry.Start, entry.End, entry.Options, t); }
```

出处：`Src/Core/VeloxDev.Core/TransitionSystem/Sampling/SamplerSet.cs:128-143`

缓动调用是 $O(1)$；采样调用是 $O(1)$ 加一个已编译 setter。稳态路径上这里不分配，因为时间通过 `Interlocked` 字段传递，应用闭包按目标缓存。合计上界为：

$$
T_{\text{frame}}(t,k) = O(t\,k) + O(t)\ \text{次宿主派发}
$$

```plot
{
  "title": "每帧代价与活跃过渡数",
  "grid": true,
  "xAxis": { "domain": [0, 20] },
  "yAxis": { "domain": [0, 400] },
  "data": [
    { "fn": "5*x", "color": "#4a9eff", "title": "每条 5 个属性" },
    { "fn": "20*x", "color": "#a78bfa", "title": "每条 20 个属性" }
  ]
}
```

## 定时器随过渡数增长，而非随属性数

没有中心帧轮。每个采样循环拥有一个可复用定时器或一个宿主节拍器；暂停的循环停在停滞等待上，不消耗唤醒。每条活跃过渡一个定时器，意味着每个帧间隔 $O(t)$ 次唤醒，间隔由效果的 `FPS` 决定（默认 60）。操作系统对定时器的合并会让真实 CPU 代价低于这个计数所暗示的水平——这是*推断*的平台效应。

## 缓动是一族常数时间函数

每个缓动都是归一化时间的纯函数，每条过渡每帧求值一次。最容易比较的是曲线——In、Out 与 InOut 的差别只在加速度放置的位置：

```plot
{
  "title": "EaseOut 家族",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [0, 1.2] },
  "data": [
    { "fn": "x", "color": "#888888", "title": "线性" },
    { "fn": "sin(x*PI/2)", "color": "#4a9eff", "title": "easeOutSine" },
    { "fn": "1 - (1-x)^3", "color": "#a78bfa", "title": "easeOutCubic" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#e5c07b", "title": "easeOutBack" }
  ]
}
```

## 重复与内存

`Repeat(n)` 让所括段范围运行 $n+1$ 次。首次迭代付出准备代价；后续迭代重放，跳过目标重读，但每次重放都构造新的解释器并惰性创建定时器。因此一条链保留 $O(\sum k_s + s)$ 的实时状态——效果、状态字典、采样项——加上每个正在执行段 $O(1)$ 的解释器与定时器。
