# 模板方法 —— 帧循环

循环骨架固定在不对外可见的 `LoopChannel` 里；可变步骤是用户的五个 `partial void` 钩子。源生成器是两者之间的桥，也正是「用户什么都不需要继承」的原因。

| 角色 | 元素 | 源码 |
|---|---|---|
| 骨架（线程路径） | `LoopChannel.UpdateLoop` | `TickManager.cs` 509-554 |
| 骨架（线程路径） | `LoopChannel.FixedUpdateLoop` | `TickManager.cs` 446-507 |
| 骨架（异步路径） | `UpdateLoopAsync` / `FixedUpdateLoopAsync` | `TickManager.cs` 622-682 / 557-620 |
| 逐行为执行 | `ExecuteBehaviorsUpdateSync` / `…LateUpdateSync` / `…FixedUpdateSync` | `TickManager.cs` 689-734 |
| 钩子方法 | `partial void Awake` / `Start` / `Update` / `LateUpdate` / `FixedUpdate` | `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` 52-168 |
| 桥接 | 生成的 `Invoke*` 方法 | `Writers/TickWriter.cs` 80-121 |
| 注册入口 | 生成的 `InitializeTickable()` / `CloseTickable()` | `Writers/TickWriter.cs` 81-89 |

## 骨架

`UpdateLoop` 就是那段不变算法。除了派发进用户代码的三行之外，其余全部固定：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（509-554 行，缩写至其形状）
private void UpdateLoop(CancellationToken token)
{
    _isUpdateThreadActive = true;
    Interlocked.Exchange(ref _updateThreadLastActivityTimestamp, GetTimestamp());

    try
    {
        while (_isRunning && !token.IsCancellationRequested)
        {
            Interlocked.Exchange(ref _updateThreadLastActivityTimestamp, GetTimestamp());

            if (!_bus.IsAdvancing)
            {
                _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
                continue;
            }

            var frameStartTime = GetTimestamp();
            ProcessMainThreadOperations();

            var sample = _updateSampler.Sample();
            if (sample.Delta == TimeSpan.Zero)
            {
                Sleep(TimeSpan.FromMilliseconds(MIN_SLEEP_MS), token);
                continue;
            }

            var frameArgs = CreateFrameEventArgs(sample.Delta, sample.Total);

            ExecuteBehaviorsUpdateSync(frameArgs, token);
            ExecuteBehaviorsLateUpdateSync(frameArgs, token);

            _frameEventArgsPool.Return(frameArgs);

            UpdatePerformanceStats(frameStartTime, sample.Total);
            FrameRateControlSync(frameStartTime, token);
            Interlocked.Increment(ref _totalFrames);
        }
    }
    catch (OperationCanceledException) { }
    finally
    {
        _isUpdateThreadActive = false;
    }
}
```

固定部分的顺序是：活动时间戳 → 停摆判定 → 主线程排空 → 采样 → 构造参数 → 派发 Update → 派发 LateUpdate → 参数还池 → 发布统计 → 限速 → 计帧。若采用继承式设计，`ExecuteBehaviors*` 会成为 `protected virtual`；这里它们是私有的，扩展点是*行为*而不是循环。没有任何东西可以继承，因为 `LoopChannel` 是 `private sealed` —— 唯一的入口是 `ITickable`。

`FixedUpdateLoop` 是另一段骨架、同一种精神：先在自己线程上落下待改的步长，做停摆判定，`Advance` 补偿采样器，然后循环推送 `count` 步，每步各自构造并归还参数（457-499 行）。

## 桥接

生成器写出了唯一同时知道两半的代码。`TickWriter.GenerateBody`（69-122 行）向用户类的分部声明中生成：

```csharp
public void InitializeTickable()
{
    global::VeloxDev.TimeLine.TickManager.SetTargetFPS(60, "demo");
    global::VeloxDev.TimeLine.TickManager.RegisterBehaviour(this, "demo");
}

public void CloseTickable()
{
    global::VeloxDev.TimeLine.TickManager.UnregisterBehaviour(this, "demo");
}

public void InvokeAwake()        { Awake(); }
public void InvokeStart()        { Start(); }
public void InvokeUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)      { Update(e); }
public void InvokeLateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)  { LateUpdate(e); }
public void InvokeFixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e) { FixedUpdate(e); }

partial void Awake();
partial void Start();
partial void Update(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void LateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void FixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
```

这份生成代码有两个性质很重要：

- **`SetTargetFPS` 那行是有条件的。** 只有当解析出的特性 FPS 为 `>= 1` 时 `TickWriter` 才拼出它（`var setFpsLine = TargetFPS >= 1 ? … : string.Empty;`，第 76 行）。写成 `[Tickable("demo")]` 时一行帧率调用都不会生成，注册就不会悄悄覆写通道设置。
- **`partial void` 声明正是钩子可选的原因。** 用户没写的钩子会被编译器整个移除，既没有空重写也没有虚调用。这是「缺失步骤零成本」的模板方法，而基于 `virtual` 的模板做不到这一点。

## 生命周期各步

注册是延迟的，这是整段模板里最容易被误读的部分。`RegisterBehaviour` 只是入队；排空发生在帧的开头、采样之前：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（785-801 行）
private void ProcessAddedBehaviors()
{
    bool added = false;
    while (_addQueue.TryDequeue(out var behavior))
    {
        if (behavior == null) continue;

        var wrapper = _wrapperPool.Get();
        wrapper.Reset(behavior, Interlocked.Increment(ref _instanceCounter));

        _behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper;
        SafeExecute(behavior.InvokeAwake);
        SafeExecute(behavior.InvokeStart);
        added = true;
    }
    if (added) _wrappersNeedSort = true;
}
```

`ProcessMainThreadOperations`（第 753 行）在 `_updateSampler.Sample()` 之前调用它，所以 `Awake` 与 `Start` 永远先于第一次 `Update` —— 无论注册发生在 `Start` 之前还是之后。WPF 演示把它变成可见的测量而不是一句主张：`SimState.AwakeAtUpdateCount` 与 `AwakeFrameOrdinal` 记录 `Awake` 运行那一刻的 `Update` 计数与引擎帧序号。

| 钩子 | 驱动者 | 频率 |
|---|---|---|
| `Awake` | update 泵，注册排空 | 每次注册一次 |
| `Start` | update 泵，紧随 `Awake` | 每次注册一次 |
| `Update` | update 泵 | 每帧 |
| `LateUpdate` | update 泵 | 每帧，在所有行为的 `Update` 之后 —— 除非 `Handled` 被置位 |
| `FixedUpdate` | fixed-update 泵 | 每步间隔（默认 16 ms），并发运行，停摆后成批补还 |

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 446-554、689-734、753-801 行；`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` 64-125 行。
