# 配置并运行循环

本步的一切都经由静态门面 `TickManager`。除 `ChannelNames` 外，每个成员都接受一个末位的可选 `channel` 参数，默认 `TickManager.DEFAULT_CHANNEL`（字面量 `"default"`）。

## 1. 先注册，再启动

```csharp
var ball = new BouncingBall();

ball.InitializeTickable();          // 生成：把该实例入队到通道 "demo"
TickManager.Start("demo");         // 创建通道并启动两条泵
```

**预期结果：** `Awake` 输出一次，随后 `Start` 输出一次，然后 `Update` / `LateUpdate` / `FixedUpdate` 开始到达。`TickManager.IsRunning("demo")` 为 `true`。

这两行的顺序无关紧要。`RegisterBehaviour` 只是*入队*；update 泵在第一帧帧体内、**该帧采样之前**排空队列。在 `Start` 之后注册也会得到同样的 `Awake` → `Start` → 首个 `Update` 序列。你无法得到的是「注册之前钩子就运行」。

`Start` 是幂等的：`LoopChannel.Start` 第一句是 `if (_isRunning) return;`（`TickManager.cs` 第 278 行），所以对运行中的通道再次 `Start("demo")` 什么也不做 —— 包括不会再次触发 `OnChannelStarted`。

## 2. 通道参数

| 调用 | 效果 | 落点 |
|---|---|---|
| `TickManager.SetTargetFPS(30, "demo")` | 目标帧率。有效范围 `1..1000`；范围外被**忽略**，不钳制。默认 60 | 入队；由 update 泵在帧边界应用 |
| `TickManager.SetFixedUpdateInterval(33, "demo")` | 两次 `FixedUpdate` 之间的毫秒数。有效范围 `1..1000`；范围外忽略。默认 16 | 写入 volatile 字段；fixed 泵在自己的线程上取走 |
| `TickManager.SetTimeScale(2f, "demo")` | 通道时钟的速率。`1.0` 为真实时间 | 直接作用于通道的时间源。**负值抛 `ArgumentOutOfRangeException`** |
| `TickManager.SetUseAsyncLoop(true, "demo")` | 用 `async`/`await` 而非原生线程驱动循环 | 存在通道上；下次 `Start` 读取。**通道运行中时抛 `InvalidOperationException`** |
| `TickManager.ClearUseAsyncLoopOverride("demo")` | 丢弃按通道覆盖，回退到 `TickManager.UseAsyncLoop` | 同样的 `InvalidOperationException` 保护 |
| `TickManager.ExecuteOnMainThread(() => ..., "demo")` | 在下一轮 update 泵开头运行委托 | 入队；每帧最多取 64 个动作 |

有两个行为常出乎意料：

- **`SetTargetFPS` 超范围时静默无操作。** `if (fps < MIN_FPS || fps > MAX_FPS) return;`（`TickManager.cs` 第 207 行）。传 `0` 或 `5000` 什么也不改，也不上报。
- **时间速率为 `0` 不是暂停。** 它冻结时钟 —— 不派发任何帧，`TotalTime` 停住 —— 但 `TickManager.IsPaused("demo")` 保持 `false`，`SystemStatus("demo")` 仍报 `"Running"`。只有非零速率能让它恢复，`Resume()` 不行。WPF 示例把 `IsAdvancing` 与 `SystemStatus` 并排打印正是为此（`MainWindow.xaml.cs` 第 276-285 行）。

**预期结果：** 调用 `SetTargetFPS(30, "demo")` 后，实测 `TickManager.CurrentFPS("demo")` 在一秒内稳定在 30 附近。调用 `SetTimeScale(2f, "demo")` 后，`TickManager.TimeScale("demo")` 返回 `2`。

## 3. 读回通道状态

| 查询 | 返回 |
|---|---|
| `IsRunning(channel)` | `bool` —— 泵已启动且未停止 |
| `IsPaused(channel)` | `bool` —— 通道时钟已暂停 |
| `SystemStatus(channel)` | `"Stopped"` / `"Paused"` / `"Running"` |
| `TargetFPS(channel)` / `CurrentFPS(channel)` | 配置值 vs. 实测帧率 |
| `TotalTime(channel)` / `TotalTimeMs(channel)` | 通道启动以来的虚拟时间 |
| `TotalFrames(channel)` | 已完成的帧数 |
| `ActiveBehaviorCount(channel)` | 当前已注册的行为数 |
| `TimeScale(channel)` | 时钟速率 |
| `IsUpdateThreadAlive(channel)` / `IsFixedUpdateThreadAlive(channel)` | `bool` —— 见下 |
| `Bus(channel)` | `ITimeSourceControl?` —— 通道时钟；通道从未创建时为 `null` |
| `ChannelNames` | `IEnumerable<string>` —— 已创建的全部通道 |

除 `ChannelNames` 外，所有查询对不存在的通道都安全：返回「已停止」的答案（`false`、`0`、`TimeSpan.Zero`、`"Stopped"`），`Bus` 则为 `null`。查询**永不创建**通道 —— `Bus` 特意返回 `null`，而不是顺手构造一个（`TickManager.cs` 第 1146-1147 行，由 `TickableBusTests.BusIsNullForAChannelThatWasNeverStarted` 断言）。

### 存活查询不是活跃度检查

`IsUpdateThreadAlive` / `IsFixedUpdateThreadAlive` 的写法是（`TickManager.cs` 第 195-199 行）：

```csharp
public bool IsUpdateThreadAlive => _isRunning && _isUpdateThreadActive &&
    (!_bus.IsAdvancing || IsRecentActivity(Interlocked.Read(ref _updateThreadLastActivityTimestamp)));
```

**暂停**中的泵 park 在时间源上而不是轮询，所以「最近 2 秒有没有活动」在暂停时必然为假。`!_bus.IsAdvancing ||` 这一项阻止它被报成线程已死。暂停通道后再查询，两者仍然返回 `true` —— `TickableBusTests.PausingAChannelStopsItsFramesAndResumingRestartsThem` 断言了这一点。

## 4. 通道事件

```csharp
TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"started {e.ChannelName}");
TickManager.OnChannelPaused  += (_, e) => Console.WriteLine($"paused  {e.ChannelName}");
TickManager.OnChannelResumed += (_, e) => Console.WriteLine($"resumed {e.ChannelName}");
TickManager.OnChannelStopped += (_, e) => Console.WriteLine($"stopped {e.ChannelName}");
```

**预期结果：** 启动通道 `demo` 时输出 `started demo`。载荷是 `TickChannelEventArgs`，唯一成员是 `ChannelName`。

这些是**静态**事件，订阅是进程范围的，所以只关心一个通道的处理器必须按 `ChannelName` 过滤。对未运行的通道调用 `StopAsync` 会提前返回（`TickManager.cs` 第 333 行，`if (!_isRunning) return;`），因此**不会**触发 `OnChannelStopped`；该事件恰好在通道从运行转为停止时触发。

## 说明

- `Start` 在首次使用时创建通道，所以对一个没有任何注册的名字调用 `TickManager.Start("demo")` 是合法的 —— 只会得到一个空循环。
- 通道线程名为 `VeloxDev.Update[<name>]` 与 `VeloxDev.FixedUpdate[<name>]`（`TickManager.cs` 第 312、318 行）。它们会出现在调试器的线程列表和示例的日志读数里。
- 停止通道会排空*队列*，但**不会**清空行为字典。已经应用过的注册在停止/启动后仍然存在并继续被驱动；只有停止时还躺在 `_addQueue` 里的注册 —— 或 `_removeQueue` 里待处理的注销 —— 会被丢弃。存活的行为不会重跑 `Awake` / `Start`。
