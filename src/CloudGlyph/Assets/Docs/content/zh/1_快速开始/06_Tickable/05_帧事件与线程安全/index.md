# 帧事件与线程安全

## 1. 钩子拿到什么

除 `Awake` 与 `Start` 外，每个钩子都收到 `FrameEventArgs`，它派生自抽象类 `TimeLineEventArgs`。两个时钟读数（`DeltaTime` / `TotalTime`）与 `Handled` 来自基类；只有两个帧率读数声明在 `FrameEventArgs` 上。

| 成员 | 类型 | 含义 |
|---|---|---|
| `DeltaTime` | `TimeSpan` | 距**同一个泵**上一次交付过去了多久，已套用时间缩放 |
| `TotalTime` | `TimeSpan` | 通道启动以来的虚拟时间；排除一切停顿 |
| `CurrentFPS` | `int` | 实测帧率，按墙钟，每墙钟秒刷新一次 |
| `TargetFPS` | `int` | 通道配置的目标帧率 |
| `Handled` | `bool` | 继承自 `TimeLineEventArgs`。置 `true` 停止本帧阶段 |

`DeltaTime` 与 `TotalTime` 声明在 `TimeLineEventArgs`（`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`），`CurrentFPS` 与 `TargetFPS` 声明在 `FrameEventArgs`（`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`）。四者都是 **`internal` setter**：钩子能读，不能写。`Handled` 是唯一可写成员。

两个时间都来自通道时钟的同一个 `TimeSample`，所以速率已经包含在内（`CreateFrameEventArgs`，`TickManager.cs` 第 826-835 行）。

## 2. `Handled` 停止本帧阶段的其余部分

```csharp
partial void Update(FrameEventArgs e)
{
    if (KeyboardInterrupt) e.Handled = true;
}
```

泵在每个行为**之前**检查该标志：

```csharp
// TickManager.cs 第 691-704 行
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

三个后果：

- `Handled` 是在**下一个**行为之前检查的 —— 置位它的行为本身不会被跳过，被跳过的是它之后的一切。
- `LateUpdate` 是独立的循环、独立的检查，所以在 `Update` 中置 `Handled` 会跳过本帧**整个** `LateUpdate` 阶段，对所有行为都如此。
- **`FixedUpdate` 不受影响。** 每个固定步都构建自己的 `FrameEventArgs`，`Update` 里置的标志永远到不了 fixed 泵。WPF 示例同时展示两半：勾上 `Handled` 后，球继续走，而由 `LateUpdate` 定位的跟随环冻住（`MainWindow.xaml.cs` 第 199-214 行）。

**预期结果：** 只注册一个行为并每帧置 `Handled` 时，`Update` 运行，`LateUpdate` 不运行。

## 3. 线程模型

| 上下文 | 线程 |
|---|---|
| `Awake`、`Start`、`Update`、`LateUpdate` | 通道的 update 线程，`VeloxDev.Update[<channel>]` |
| `FixedUpdate` | 通道的 fixed-update 线程，`VeloxDev.FixedUpdate[<channel>]` |
| `TickManager.Start` / `Pause` / `Resume` / `SetTargetFPS` / `RegisterBehaviour` / … | 调用它的任意线程 —— 从任何线程调用都安全 |
| `TickManager.ExecuteOnMainThread(action, channel)` | 委托在**update** 线程上下一次迭代开头运行 |

两条泵是独立线程且**并发**执行：一个 `FixedUpdate` 函数体与一个 `Update` 函数体可能在同一瞬间运行，所以两者都会碰的字段必须自行同步。示例用*归属*而不是锁解决 —— 每个球只由一条泵线程独占，窗口从不碰它（`SimState.cs`）。唯一跨线程的状态是整份发布的：

| 通道 | 机制 |
|---|---|
| 球快照 | 不可变 `BallReport`，`Volatile.Write` 写、`Volatile.Read` 读 |
| 计数器 | `Interlocked` |
| 日志 | `ConcurrentQueue`（`DemoState`） |

框架不替你做任何一件这样的事情。

`ExecuteOnMainThread` 里的「主线程」指*update 泵线程*，不是 UI 线程。在 GUI 宿主里你仍要自己封送到 dispatcher —— 而且不要在钩子里做，因为引擎会捕获钩子抛出的一切异常并且只写 `Debug.WriteLine`。因此一个抛异常的 `Dispatcher.Invoke` 是**屏幕上没有症状、日志里也没有记录**的失败。WPF 示例通过让钩子发布不可变快照、由 UI 线程轮询来绕开整类问题（`MainWindow.Hooks.cs` 第 173-193 行，`MainWindow.xaml.cs` 第 142-154 行）。

## 4. 异常隔离

每次钩子调用都被包住：

```csharp
try { w.Behavior.InvokeUpdate(frameArgs); }
catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
```

- 一个行为抛异常**不会**停下循环，也**不会**阻止其他行为运行。
- 唯一痕迹是 `Debug.WriteLine`，它在 Release 构建中被编译掉。Release 下抛异常的钩子悄无声息。
- 生成的 `Awake` 与 `Start` 走等价的保护（`SafeExecute`，`TickManager.cs` 第 941-944 行）。

**预期结果：** 每帧都抛异常的钩子不会停下循环，`TotalFrames` 继续增长；在附加调试器的 Debug 构建中，Output 窗口每帧出现一行。

## 5. 需要跨线程标志时

`FrameEventArgs` 是普通类，`Handled` 是普通 `bool`，没有内存屏障。这是安全的，因为泵读它、钩子写它，发生在**同一个**线程 —— 在框架内部 `Handled` 从不跨线程。每次构建参数时它都被重置为 `false`（`TickManager.cs` 第 833 行），所以帧与帧之间不携带任何状态。

框架里没有 `ThreadSafeFrameEventArgs`；它已从源码中移除。如果你自己的代码必须观察另一线程置起的标志，不要从那个线程写 `FrameEventArgs.Handled`。用 `Volatile.Write` 发布标志、用 `Volatile.Read` 读取 —— 框架处理跨线程 `_targetFPS` 时就是这个写法（写在第 778 行，读在第 832 行）—— 然后在钩子里、在泵线程上把它转成 `Handled`：

```csharp
// 宿主状态，由另一线程写：
private int _stopRequested;                          // 0 / 1
public void RequestStop() => Volatile.Write(ref _stopRequested, 1);

// 钩子里 —— 运行在泵线程上：
partial void Update(FrameEventArgs e)
{
    if (Volatile.Read(ref _stopRequested) != 0) e.Handled = true;
}
```

`Handled` 仍然是泵线程上的单线程写；只有宿主标志跨线程，而且走的是正规屏障。记住 `Handled` 只停止当前帧阶段（第 2 节）。要结束循环本身，请调用 `TickManager.Pause(channel)` / `StopAsync(channel)` —— 生命周期调用从任何线程都安全。

## 说明

- 如果 fixed 泵需要同一把锁，不要在 `Update` 整个函数体持有它；16 ms 的步长下，fixed 泵会排在后面，你的 `FixedUpdate` 次数会下降。
- 不要在钩子里调用 `Thread.Sleep` 并指望循环干净地补偿。`Update` 不补偿 —— 睡眠会以一次巨大的 `DeltaTime` 出现在**下一帧**，因为采样发生在钩子之前。`FixedUpdate` *会*补偿 —— 睡眠会变成下一次 advance 的一批步。WPF 示例为两种情况各有一个按钮（`MainWindow.xaml.cs` 第 88-92 行），并用 `HookNote.Slept` / `HookNote.AfterSleep` 区分（`MainWindow.Hooks.cs` 第 68-83、141-153 行）。
