# 对象池与写时复制派发

每帧原本会分配一个 `FrameEventArgs`、每次帧率变更一个 `ConfigChangeRequest`、每次注册一个 wrapper。三者都以固定容量池化，循环读取的派发数组是按变更复制的快照。设计目标是稳态帧零分配。

| 池 | 元素类型 | 容量 | 源码 |
|---|---|---|---|
| `_frameEventArgsPool` | `FrameEventArgs` | `DEFAULT_OBJECT_POOL_SIZE` = 50 | `TickManager.cs` 154 |
| `_configRequestPool` | `ConfigChangeRequest` | 50 | `TickManager.cs` 155 |
| `_wrapperPool` | `BehaviorWrapper` | 50 | `TickManager.cs` 156 |

## 池

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 71-95 行）
private sealed class ObjectPool<T>(int maxSize) where T : class, new()
{
    private readonly ConcurrentStack<T> _pool = new();
    private int _count;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public T Get()
    {
        if (_pool.TryPop(out var item))
        {
            Interlocked.Decrement(ref _count);
            return item;
        }
        return new T();
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public void Return(T item)
    {
        if (Interlocked.Increment(ref _count) <= maxSize)
            _pool.Push(item);
        else
            Interlocked.Decrement(ref _count);
    }
}
```

实现中有三点是刻意的：

- **`Get` 在有货时零分配，未命中时分配。** 没有阻塞、没有等待队列：池空就 `new T()`，热路径永不卡住。
- **上限只在 `Return` 上执行。** 自增是无条件的，所以并发下计数保持准确；超出部分减回去、对象交给 GC。池因此在突发下*收缩*，而不是无限增长。
- **计数器是 `int` + `Interlocked`，不是 `_pool.Count`。** `ConcurrentStack<T>.Count` 会遍历栈；这里是 O(1)。

## 池被触碰的地方

`FrameEventArgs` 每帧取一次，并在同一帧函数体结束前归还：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 826-835 行）
private FrameEventArgs CreateFrameEventArgs(TimeSpan delta, TimeSpan total)
{
    var frameArgs = _frameEventArgsPool.Get();
    frameArgs.DeltaTime = delta;
    frameArgs.TotalTime = total;
    frameArgs.CurrentFPS = _currentFPS;
    frameArgs.TargetFPS = Volatile.Read(ref _targetFPS);
    frameArgs.Handled = false;
    return frameArgs;
}
```

`Handled = false` 是让复用安全的复位，也是按帧阶段中止可靠的原因：每一帧都从已知干净的标志开始。

fixed 泵**每步**取还一次参数，而不是每次唤醒一次 —— 一次欠六步的停摆会在同一轮循环里取六次，并立即逐个归还：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 485-495 行）
for (var i = 0; i < count; i++)
{
    var fixedFrameArgs = CreateFrameEventArgs(
        sample.Delta,
        TimeSpan.FromTicks((firstStep + i) * stepTicks));
    ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);

    // 直接还池。这里原来把它塞进一个跨线程队列，由 update 循环取出再还池——
    // 一次往返，而那条队列从不把参数交给任何人，纯粹是浪费。
    _frameEventArgsPool.Return(fixedFrameArgs);
}
```

那段注释记录了一次被移除的往返：参数原本被交给一个跨线程队列，update 循环排空它只是为了还池，从来没有人从该队列读取参数。

`ConfigChangeRequest` 是唯一跨线程的池化对象 —— 由 `SetTargetFPS` 在调用者线程取出、填充、入队，稍后由 update 泵重置并归还（`ProcessConfigChanges`，第 770-785 行，以及 `ClearQueues`，第 956-967 行）。

`BehaviorWrapper` 按注册池化：在 `ProcessAddedBehaviors` 中取出并 `Reset`（第 794-795 行），在 `ProcessRemovedBehaviors` 中 `Clear` 并归还（第 812-813 行）。

## 为什么只池化三样

两个过去需要池化请求对象的旋钮现在不需要了，代码里写明原因：

- `SetFixedUpdateInterval` 写一个 volatile 字段。请求对象只在值必须经过 update 泵队列时才存在；现在它直接交给拥有采样器的泵。
- `SetTimeScale` 写给 bus，bus 自己串行化写入者。

`ConfigChangeRequest` 只为 `TargetFPS` 保留，因为这一项确实必须由 update 循环应用：目标与缓存帧时长必须一起写，而两者都只有 update 循环会读。

## 写时复制派发

循环从不遍历行为字典，而是遍历一个仅在变更时重建的普通数组：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 743-753 行）
private BehaviorWrapper[] GetCachedWrappers()
{
    var currentTime = GetTimestamp();
    if (_wrappersNeedSort || currentTime - Interlocked.Read(ref _lastConfigCheckTimestamp) >
        TimeConversion.MillisecondsToTicks(MAX_CONFIG_CACHE_DURATION_MS, TimeConversion.DefaultTicksPerSecond))
    {
        RebuildCachedWrappers();
        Interlocked.Exchange(ref _lastConfigCheckTimestamp, currentTime);
    }
    return _cachedWrappers;
}
```

重建（第 874-903 行）是有意思的决定所在：

- 它按 `_behaviors.Values.Count` 定长，填入活跃 wrapper，**按 `ExecutionOrder` 插入排序**，再 `Array.Resize` 缩短。源码注释说明了选择插入排序的理由：行为数量通常很小，LINQ 会分配。
- `_cachedWrappers` 是 `volatile`，所以调用 `GetCachedWrappers` 的泵线程要么看到完整数组、要么看到上一个完整数组 —— 永远不会看到半成品。派发路径上完全没有锁。
- `_wrappersNeedSort` 由新增/移除排空置位、由重建清除，所以注册对下一帧立即可见。

派发循环因此是在稳定数组上的裸索引 `for`，`Handled` 与取消检查内联在每次迭代：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 691-704 行）
private void ExecuteBehaviorsUpdateSync(FrameEventArgs frameArgs, CancellationToken token)
{
    var wrappers = GetCachedWrappers();
    for (int i = 0; i < wrappers.Length; i++)
    {
        if (frameArgs.Handled || token.IsCancellationRequested) break;
        var w = wrappers[i];
        if (w is { IsActive: true, Behavior: not null })
        {
            try { w.Behavior.InvokeUpdate(frameArgs); }
            catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
        }
    }
}
```

循环内的 `try/catch` 就是异常隔离策略：一个行为失常不能停下循环，也不能阻止它后面的行为。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 71-95、154-156、485-495、691-704、743-753、770-818、826-835、874-903、956-967 行。
