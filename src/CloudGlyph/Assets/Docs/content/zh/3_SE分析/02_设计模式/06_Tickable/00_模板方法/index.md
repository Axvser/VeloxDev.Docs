# 模板方法 —— 帧循环

循环骨架固定在私有的 `LoopChannel` 内；可变步骤是用户的五个 `partial void` 钩子。源生成器是两者之间的桥，也正是用户从不继承任何东西的原因。

| 角色 | 元素 | 源码 |
|---|---|---|
| 骨架（线程路径） | `LoopChannel.UpdateLoop` | `TickManager.cs` 511-556 |
| 骨架（线程路径） | `LoopChannel.FixedUpdateLoop` | `TickManager.cs` 448-509 |
| 骨架（异步路径） | `UpdateLoopAsync` / `FixedUpdateLoopAsync` | `TickManager.cs` 624-684 / 559-622 |
| 按行为执行 | `ExecuteBehaviorsUpdateSync` / `…LateUpdateSync` / `…FixedUpdateSync` | `TickManager.cs` 691-736 |
| 钩子方法 | `partial void Awake` / `Start` / `Update` / `LateUpdate` / `FixedUpdate` | `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` 45-161 |
| 桥 | 生成的 `Invoke*` 方法 | `Writers/TickWriter.cs` 74-127 |
| 注册入口 | 生成的 `InitializeTickable()` / `CloseTickable()` | `Writers/TickWriter.cs` 85-94 |

## 骨架

`UpdateLoop` 是不变算法。除了分派进用户代码的三行，里面的一切都是固定的：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 511-556 行，按形状节选）
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

固定部分依次为：活动时间戳 → 停摆检查 → 主线程排空 → 采样 → 构建参数 → 派发 Update → 派发 LateUpdate → 参数还池 → 发布统计 → 节拍控制 → 帧计数。基于子类的设计会把 `ExecuteBehaviors*` 放在 `protected virtual` 后面；这里它们是私有的，扩展点是*行为*，不是循环。没有东西可以继承，因为 `LoopChannel` 是 `private sealed` —— 唯一入口是 `ITickable`。

`FixedUpdateLoop` 是另一种骨架、同样的精神：在自己的线程上应用待定的步长变更，停摆检查，`Advance` 补偿采样器，然后循环推送 `count` 步，每步构建并立即归还自己的参数（第 459-501 行）。

## 桥

生成器写出唯一同时了解两半的代码。`TickWriter.GenerateBody`（第 74-127 行）把下面的内容写进用户类的 partial 声明：

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

生成代码有两点重要：

- **`SetTargetFPS` 那行是有条件的。** 仅当解析出的特性 FPS `>= 1` 时才构建（`var setFpsLine = TargetFPS >= 1 ? … : string.Empty;`，第 81 行）。写成 `[Tickable("demo")]` 时完全不生成帧率调用，注册不会悄悄覆盖通道设置。
- **`partial void` 声明让钩子可选。** 用户没写的方法被编译器移除，没有空重写，也没有虚调用。这是带*零成本*缺失步骤的模板方法 —— 基于 `virtual` 的模板做不到。

## 生命周期步骤

注册是延迟的，这是模板中最容易误读的部分。`RegisterBehaviour` 只入队；排空发生在帧顶部、采样之前：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 787-803 行）
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

`ProcessMainThreadOperations`（第 755 行）在 `_updateSampler.Sample()` 之前调用它，所以 `Awake` 与 `Start` 总在第一个 `Update` 之前 —— 无论注册发生在 `Start` 之前还是之后。WPF 示例把它变成可见的测量而不是断言：`SimState.AwakeAtUpdateCount` 与 `AwakeFrameOrdinal` 记录 `Awake` 运行时的 `Update` 计数器与引擎帧序号。

| 钩子 | 驱动者 | 频率 |
|---|---|---|
| `Awake` | update 泵，注册排空 | 每次注册一次 |
| `Start` | update 泵，紧接 `Awake` | 每次注册一次 |
| `Update` | update 泵 | 每帧 |
| `LateUpdate` | update 泵 | 每帧，在所有行为的 `Update` 之后 —— 除非 `Handled` 被置位 |
| `FixedUpdate` | fixed-update 泵 | 每个步长（默认 16 ms），并发，停摆后成批补还 |

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 448-556、691-736、755-803 行；`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` 第 74-127 行。
