# 05 · 帧事件与线程安全

## 1. 钩子收到什么

除 `Awake` 与 `Start` 外，每个钩子都会收到一个 `FrameEventArgs`，它派生自抽象类 `TimeLineEventArgs`。

| 成员 | 类型 | 含义 |
|---|---|---|
| `DeltaTime` | `TimeSpan` | 距离**本泵**上一帧的时间，已计入时间速率 |
| `TotalTime` | `TimeSpan` | 通道启动以来的虚拟时间。不含一切停摆期；它由时钟拥有，不是你收到的各次 delta 之和 |
| `CurrentFPS` | `int` | 实测帧率，基于墙钟，每秒刷新一次 |
| `TargetFPS` | `int` | 通道配置的目标帧率 |
| `Handled` | `bool` | 继承自 `TimeLineEventArgs`。置为 `true` 可中止本帧阶段 |

`DeltaTime`、`TotalTime`、`CurrentFPS`、`TargetFPS` 四者的 setter 都是 **`internal`**（`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs` 第 10-25 行）。你可以在钩子里读，但写不了。`Handled` 是唯一可写的成员，也正是唯一一个你会想去写的。

两个时间取自通道时钟上的同一次 `TimeSample`，所以速率已经在它们里面了（`CreateFrameEventArgs`，`TickManager.cs` 第 824-833 行）—— 泵之后不会再对任何值做缩放。

## 2. `Handled` 中止本帧阶段的其余部分

```csharp
partial void Update(FrameEventArgs e)
{
    if (KeyboardInterrupt) e.Handled = true;
}
```

泵是在每个行为**之前**检查这个标志，而不是之后：

```csharp
// TickManager.cs 第 688-702 行
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

由此有三条推论：

- `Handled` 是在置位它的那个行为**之前**被检查的 —— 所以置位者自己不会被跳过，被跳过的是它后面的一切。
- `LateUpdate` 是另一个循环、另一次检查，因此在 `Update` 里置 `Handled` 会跳过本帧对**所有**行为的**整个** `LateUpdate` 阶段。
- **`FixedUpdate` 不受影响。** 每个固定步各自构造一个 `FrameEventArgs`，所以 `Update` 里立起的标志对 fixed 泵永远不可见。WPF 演示把两半都演示了出来：打开 `Handled` 后两只球继续走，而由 `LateUpdate` 定位的跟随环冻住。

**预期结果：** 只注册一个行为并每帧置 `Handled` 时，`Update` 照跑而 `LateUpdate` 不跑。`06_验证与完整代码` 里的无头运行记录到 `Update +7 LateUpdate +0`。

## 3. 线程模型

| 位置 | 线程 |
|---|---|
| `Awake`、`Start`、`Update`、`LateUpdate` | 通道的 Update 线程，`VeloxDev.Update[<通道名>]` |
| `FixedUpdate` | 通道的 FixedUpdate 线程，`VeloxDev.FixedUpdate[<通道名>]` |
| `TickManager.Start` / `Pause` / `Resume` / `SetTargetFPS` / `RegisterBehaviour` / … | 调用它的那个线程 —— 从任意线程调用都安全 |
| `TickManager.ExecuteOnMainThread(action, channel)` | 委托在**Update**线程上、于下一帧开头运行 |

两个泵是两条独立线程、**并发**执行。一个 `FixedUpdate` 函数体与一个 `Update` 函数体可能在同一瞬间运行，所以任何被两者触碰的字段都要自己做同步。演示靠的是**所有权**而不是锁：每只球都由恰好一条泵线程独占，窗口从不触碰它 —— `SimState.cs` 的原话就是「No locking anywhere: exactly one pump thread owns each instance and the window never touches one」。唯一需要跨线程的状态是整体发布的：一个不可变的 `BallReport` 快照用 `Volatile.Write` 写、用 `Volatile.Read` 读，再加上 `Interlocked` 计数器与 `ConcurrentQueue` 日志（`DemoState`，`SimState.cs` 第 191-279 行）。框架不会替你处理这些。

`ExecuteOnMainThread` 里的「主线程」指的是 **Update 泵的线程**，不是 UI 线程。在 GUI 宿主里你仍然要自己封送到 dispatcher —— 而且不要在钩子里做，因为引擎会捕获钩子抛出的一切异常并只写进 `Debug.WriteLine`。一个抛异常的 `Dispatcher.Invoke` 因此是**屏幕上没有症状、任何日志里也没有记录**的失败。WPF 演示用「钩子发布不可变快照、UI 线程轮询」绕开了整类问题（`MainWindow.Hooks.cs` 第 15-22 行）。

## 4. 异常隔离

每次钩子调用都被包住：

```csharp
try { w.Behavior.InvokeUpdate(frameArgs); }
catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
```

- 一个行为里的异常**不会**停下循环，也**不会**阻止其他行为继续运行。
- 唯一的痕迹是 `Debug.WriteLine`，而它在 Release 构建里会被编译掉（框架没有设置 `DEBUG` 常量；`Debug.WriteLine` 取决于你程序集的配置）。在 Release 里，抛异常的钩子是静默的。
- 生成的 `Awake` 与 `Start` 走的是同等的保护（`SafeExecute`，`TickManager.cs` 第 939-942 行）。

**预期结果：** 一个每帧都抛异常的钩子会让循环继续运行、`TotalFrames` 继续增长；在挂着调试器的 Debug 构建里，Output 窗口每个异常一行。

## 5. 什么时候需要线程安全标志

`FrameEventArgs` 是普通类，它的 `Handled` 就是普通 `bool`，没有任何内存屏障。泵线程读、你在泵线程写，所以在单个钩子内部它是安全的。如果你想从**另一个线程**立起这个标志，就用 `ThreadSafeFrameEventArgs`，它用一把锁包住该属性（`Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`）：

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    private readonly object _lockObject = new();
    private bool _handled;

    public new bool Handled
    {
        get { lock (_lockObject) return _handled; }
        set { lock (_lockObject) _handled = value; }
    }
}
```

注意框架自己从不构造这个类型 —— 交给钩子的每个 `FrameEventArgs` 都是从通道池里取出的普通 `FrameEventArgs`。它是给「自建事件参数的宿主」用的；而 `new` 关键字意味着，通过 `FrameEventArgs` 引用去读一个 `ThreadSafeFrameEventArgs`，拿到的是**未同步**的那个属性。要么用它的静态类型引用来使用，要么就别用。

## 说明

- 如果 fixed 泵需要同一把锁，就不要在整个 `Update` 函数体上持锁；16 ms 的步长下 fixed 泵会被它挡住，你的 `FixedUpdate` 计数会掉。
- 不要指望在钩子里 `Thread.Sleep` 之后循环能干净地补偿。`Update` 是不补偿的 —— 那里的睡眠会以**下一帧**一个巨大的 `DeltaTime` 出现，因为采样发生在钩子运行之前。`FixedUpdate` **是**补偿的 —— 那里的睡眠会在下一次 advance 时变成一批步。WPF 演示为两者各配了一个按钮，它们之间的差别就是这个演示的主题。
