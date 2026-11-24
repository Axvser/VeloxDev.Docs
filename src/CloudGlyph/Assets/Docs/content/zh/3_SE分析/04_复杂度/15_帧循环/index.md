# 帧循环

每个通道在专用线程（WASM 上为两个任务）上跑两个循环：一个更新循环，每帧把每个活跃行为派发一次；一个固定循环，追赶错过的步。每帧代价对已注册行为线性。固定循环更有意思，因为追赶受两重限制——每次调用与累计欠步。

记号：通道内活跃行为 $b$，一次调用推进的固定步 $c$，生命周期/错误订阅者 $s$，排队主线程动作 $a$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| 更新帧 | $O(b) + O(64 + a)$ | $O(b)$ 缓存数组 | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:511` |
| 固定更新，一次调用 | $O(c b)$，$c \le 8$ | 每步 $O(1)$ | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:478` |
| 注册 / 注销 | $O(1)$ 入队 + $O(1)$ 应用 | $O(1)$ | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:432` |
| 包装器缓存重建 | 均摊 $O(b \log b)$，最坏 $O(b^2)$，每秒至多一次 | 新的 $O(b)$ 数组 | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:874` |
| 通道查找 | 均摊 $O(1)$ | — | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:1021` |
| 时间线采样 | $O(1)$ | — | `Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs:433` |
| 错误报告 | $O(s)$ + 异常 | — | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:1052` |

## 每帧对缓存数组一遍

更新遍遍历缓存包装器数组，若某行为设置 `Handled` 则停止当前遍：

```csharp
var wrappers = GetCachedWrappers();
for (int i = 0; i < wrappers.Length; i++)
{
    if (frameArgs.Handled || token.IsCancellationRequested) break;
    var w = wrappers[i];
    if (w is { IsActive: true, Behavior: not null })
    {
        try { w.Behavior.InvokeUpdate(frameArgs); }
        catch (Exception ex) { ReportBehaviorError(Name, "Update", ex); }
    }
}
```

出处：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:693-703`

有 Update 与 LateUpdate 两遍，所以最坏一帧是 $2b$ 次派发。包装器数组只在注册变化或缓存超过一秒时重建，重建按执行顺序做插入排序。于是稳态帧是 $O(b)$，摊还 $O(b \log b)$ 次重建。

## 固定更新会追赶，但有上限

采样器返回欠多少固定步，循环为每一步构造自己的帧参数：

```csharp
var count = _fixedSampler.Advance(out var sample);
if (count > 0)
{
    ...
    for (var i = 0; i < count; i++)
    {
        var fixedFrameArgs = CreateFrameEventArgs(...);
        ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);
        _frameEventArgsPool.Return(fixedFrameArgs);
    }
}
```

出处：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:478-496`

两个上限约束 $c$。`MaxStepsPerCall`（8）限制每次调用的步数；`MaxPendingSteps`（64）限制保留的欠步，超出部分被宽恕并计为丢弃。因此一次长时间卡顿在下次调用中至多花费 $8b$ 次派发：

$$
T_{\text{fixed}} = O(c\,b),\qquad c \le 8
$$

```plot
{
  "title": "每次调用的固定更新派发",
  "grid": true,
  "xAxis": { "domain": [0, 100] },
  "yAxis": { "domain": [0, 800] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "每帧一步，b 个行为" },
    { "fn": "8*x", "color": "#f472b6", "title": "追赶上限，c = 8" }
  ]
}
```

步总数由已投递的整数计数导出，而不是由墙钟余数，所以固定循环不会在追赶爆发后漂移。

## 哪些不在每帧路径上

订阅者不在帧路径上。通道生命周期事件与错误报告在每次转变或错误时调用处理器，$O(s)$；行为从数组派发，不经过事件。总线是被 $O(1)$ 采样的共享时间线；暂停与速率通过停滞门传播，停滞的循环完全不派发。注册只是入队，在下一帧以 $O(1)$ 应用。

## 内存与语义

通道为每个活跃行为保存一个包装器，以及一个按分配重建的缓存数组。每个队列保存待处理的注册或动作，三个对象池上限各 50。使用 OS 线程路径时，每通道两个专用线程是真正的固定成本；异步路径避免它们。注意 `Handled` 每帧重置，只中断当前遍——在 Update 中设置它会跳过 LateUpdate 遍，但不会停止通道。
