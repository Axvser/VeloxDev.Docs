# 对象池与写时复制派发

若不池化，每帧会分配一个 `FrameEventArgs`，每次帧率变更分配一个 `ConfigChangeRequest`，每次注册分配一个包装器。三者都按固定容量池化，循环读取的派发数组则是变更时复制的快照。设计目标是：稳态下每帧零分配。

| 池 | 元素类型 | 容量 | 源码 |
|---|---|---|---|
| `_frameEventArgsPool` | `FrameEventArgs` | `DEFAULT_OBJECT_POOL_SIZE` = 50 | `TickManager.cs` 152 |
| `_configRequestPool` | `ConfigChangeRequest` | 50 | `TickManager.cs` 153 |
| `_wrapperPool` | `BehaviorWrapper` | 50 | `TickManager.cs` 154 |

## 池本身

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（69-93 行）
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

其中三处细节是刻意的：

- **`Get` 在有货时零分配，缺货时分配。** 没有阻塞、没有等待队列：池空即 `new T()`，热路径永不卡顿。
- **上限只在 `Return` 上把关。** 自增是无条件的，所以并发下计数始终准确；超出的部分再自减回去，该对象交给 GC。于是池在突发流量下会*收缩*，而不是无界增长。
- **计数是 `int` 加 `Interlocked`，不是 `_pool.Count`。** `ConcurrentStack<T>.Count` 需要遍历栈；这里读的是 O(1)。

## 池在哪里被触碰

`FrameEventArgs` 每帧取一次，并在同一帧帧体结束时归还：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（824-833 行）
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

`Handled = false` 这一行就是让复用安全的复位，也是逐帧阶段中止可靠的原因：每一帧都从一个已知干净的标志出发。

fixed 泵是**每步**取还一个参数，而不是每次唤醒一个 —— 一次停摆欠六步，就在一次循环迭代里取六次、每次都立刻归还：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（483-493 行）
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

这段注释记录了一次被移除的往返：参数原本被交给一条跨线程队列，由 update 循环取出、只为把它们还池。从来没有谁从那条队列读过这些参数。

`ConfigChangeRequest` 是唯一跨线程的池化对象 —— 由 `SetTargetFPS` 在调用方线程取出并填充，入队，随后由 update 泵复位并归还（`ProcessConfigChanges` 768-783 行，`ClearQueues` 954-965 行）。

`BehaviorWrapper` 按注册池化：在 `ProcessAddedBehaviors` 中取出并 `Reset`（792-793 行），在 `ProcessRemovedBehaviors` 中 `Clear` 并归还（810-811 行）。

## 为什么只池化这三样

两个曾经需要池化请求对象的旋钮现在不需要了，代码给出了理由：

- `SetFixedUpdateInterval` 只写一个 volatile 字段。请求对象只在数值必须经由 update 泵的队列传递时才存在；现在它直接送到拥有采样器的那个泵。
- `SetTimeScale` 写到总线上，而总线自己串行化它的写入者。

`ConfigChangeRequest` 只为 `TargetFPS` 留下，因为这一项确实必须由 update 循环施加：目标帧率与缓存的帧时长必须一起写，而两者都只有 update 循环读。

## 写时复制派发

循环从不遍历行为字典，而是遍历一个仅在发生变化时才重建的普通数组：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（741-751 行）
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

重建过程（872-901 行）里才是有意思的决定：

- 先按 `_behaviors.Values.Count` 开数组，把活跃包装器填进去，**按 `ExecutionOrder` 做插入排序**，最后 `Array.Resize` 缩小。源码注释点明了选插入排序的理由：行为数通常很小，而 LINQ 会产生分配。
- `_cachedWrappers` 是 `volatile`，所以调用 `GetCachedWrappers` 的泵线程看到的是完整数组或上一个完整数组，绝不会看到构造到一半的。派发路径上完全没有锁。
- `_wrappersNeedSort` 由新增与移除的排空过程置位、由重建清除，因此一次注册对下一帧即已可见。

于是派发循环就是在稳定数组上裸索引的 `for`，`Handled` 与取消检查逐次内联：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（689-702 行）
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

循环体内的 `try/catch` 就是异常隔离策略：一个出问题的行为无法停下循环，也无法影响排在它后面的行为。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 69-93、152-154、483-493、689-702、741-751、768-816、824-833、872-901、954-965 行。
