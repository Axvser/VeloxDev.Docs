# 03 · 运行与配置循环

本步骤的一切都经由静态门面 `TickManager`。它的每个成员都带一个可选的末位 `channel` 参数，默认值为 `TickManager.DEFAULT_CHANNEL`（字面量 `"default"`）。

## 1. 先注册，再启动

```csharp
var ball = new BouncingBall();

ball.InitializeTickable();          // 生成的方法：把本实例入队到通道 "demo"
TickManager.Start("demo");         // 创建通道并启动两个泵
```

**预期结果：** `Awake` 打印一次，随后 `Start` 打印一次，接着 `Update` / `LateUpdate` / `FixedUpdate` 开始到达。`TickManager.IsRunning("demo")` 为 `true`。

这两行的先后顺序无关紧要，这一点值得说清楚。`RegisterBehaviour` 只是**入队**；Update 泵会在自己的第一帧帧体内排空队列，**早于**该帧被采样。所以启动之后再注册，依然得到 `Awake` → `Start` → 第一次 `Update`；启动之前注册也一样。你唯一拿不到的，是「钩子先于注册运行」。

`Start` 是幂等的：`LoopChannel.Start` 第一句就是 `if (_isRunning) return;`（`TickManager.cs` 第 276 行），所以对运行中的通道再调一次 `Start("demo")` 什么都不会发生 —— 连 `OnChannelStarted` 也不会再触发。

## 2. 通道配置旋钮

| 调用 | 作用 | 生效位置 |
|---|---|---|
| `TickManager.SetTargetFPS(30, "demo")` | 目标帧率。有效范围 `1..1000`，超范围**被忽略**，不是被钳制。默认 60 | 入队；在下一个帧边界生效 |
| `TickManager.SetFixedUpdateInterval(33, "demo")` | 两次 `FixedUpdate` 之间的毫秒数。有效范围 `1..1000`，超范围忽略。默认 16 | 写入一个 volatile 字段；由 fixed 泵在自己的线程上取走 |
| `TickManager.SetTimeScale(2f, "demo")` | 通道时钟的速率。`1.0` 为真实时间 | 直接作用于通道的时间源。**负值抛 `ArgumentOutOfRangeException`** |
| `TickManager.SetUseAsyncLoop(true, "demo")` | 改用 `async`/`await` 而非原生线程驱动循环 | 存在通道上。**通道运行中会抛 `InvalidOperationException`** |
| `TickManager.ClearUseAsyncLoopOverride("demo")` | 清除按通道的覆盖，回退到 `TickManager.UseAsyncLoop` | 同样的 `InvalidOperationException` 保护 |
| `TickManager.ExecuteOnMainThread(() => ..., "demo")` | 在下一帧开头运行该委托 | 入队；每帧最多排空 64 个动作 |

其中两项的行为与「想当然的读法」不同：

- **`SetTargetFPS` 超范围时是静默 no-op。** `if (fps < MIN_FPS || fps > MAX_FPS) return;`（`TickManager.cs` 第 205-206 行）。传 `0` 或 `5000` 什么都不改，也什么都不告诉你。
- **时间速率 `0` 不是暂停。** 它冻结时钟 —— 不再派发任何帧，`TotalTime` 停住 —— 但 `TickManager.IsPaused("demo")` 仍为 `false`，`SystemStatus("demo")` 仍报 `"Running"`。只有非零速率能让它重新走起来，`Resume()` 做不到。WPF 演示正是为此把 `IsAdvancing` 与 `SystemStatus` 并排打印（`MainWindow.xaml.cs` 第 307-324 行）。

**预期结果：** 调用 `SetTargetFPS(30, "demo")` 后，实测的 `TickManager.CurrentFPS("demo")` 会在一秒内稳定在 30 附近。调用 `SetTimeScale(2f, "demo")` 后，`TickManager.TimeScale("demo")` 返回 `2`。

## 3. 把通道读回来

| 查询 | 返回 |
|---|---|
| `IsRunning(channel)` | `bool` —— 泵已启动且未停止 |
| `IsPaused(channel)` | `bool` —— 通道时钟处于暂停 |
| `SystemStatus(channel)` | `"Stopped"` / `"Paused"` / `"Running"` |
| `TargetFPS(channel)` / `CurrentFPS(channel)` | 配置的帧率 / 实测帧率 |
| `TotalTime(channel)` / `TotalTimeMs(channel)` | 通道启动以来的虚拟时间 |
| `TotalFrames(channel)` | 已完成的帧数 |
| `ActiveBehaviorCount(channel)` | 当前已注册的行为数 |
| `TimeScale(channel)` | 时钟速率 |
| `IsUpdateThreadAlive(channel)` / `IsFixedUpdateThreadAlive(channel)` | `bool` —— 见下面的说明 |
| `Bus(channel)` | `ITimeSourceControl?` —— 通道的时钟；通道从未创建时为 `null` |
| `ChannelNames` | `IEnumerable<string>` —— 已创建的全部通道名 |

除 `ChannelNames` 外，所有查询对不存在的通道都安全：返回「已停止」的答案（`false`、`0`、`TimeSpan.Zero`、`"Stopped"`），`Bus` 则返回 `null`。查询**永远不会创建**通道 —— `Bus` 特意写成宁可答 `null` 也不顺手造一个（`TickManager.cs` 第 1134-1145 行，并由 `TickableBusTests.BusIsNullForAChannelThatWasNeverStarted` 断言）。

### 存活查询不是「活跃度」检查

`IsUpdateThreadAlive` / `IsFixedUpdateThreadAlive` 的实现是：

```csharp
public bool IsUpdateThreadAlive => _isRunning && _isUpdateThreadActive &&
    (!_bus.IsAdvancing || IsRecentActivity(Interlocked.Read(ref _updateThreadLastActivityTimestamp)));
```

**暂停中**的泵 park 在时间源上而不是轮询，所以「它最近 2 秒有没有干活」在暂停时必然为假。`!_bus.IsAdvancing ||` 这一项就是用来阻止把这种情况报成线程已死的。实测：暂停一个通道后再查询，两个都仍返回 `true` —— 见 `TickableBusTests.PausingAChannelStopsItsFramesAndResumingRestartsThem` 与 `06_验证与完整代码` 中的那次运行。

## 4. 通道事件

```csharp
TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"started {e.ChannelName}");
TickManager.OnChannelPaused  += (_, e) => Console.WriteLine($"paused  {e.ChannelName}");
TickManager.OnChannelResumed += (_, e) => Console.WriteLine($"resumed {e.ChannelName}");
TickManager.OnChannelStopped += (_, e) => Console.WriteLine($"stopped {e.ChannelName}");
```

**预期结果：** 启动通道 `demo` 会打印 `started demo`。载荷是 `TickChannelEventArgs`，其唯一成员是 `ChannelName`。

这些是**静态**事件，订阅是进程范围的，因此只关心某一个通道的处理器必须按 `ChannelName` 过滤。另外注意：若通道当时并未运行，`StopAsync` 会在开头提前返回（`TickManager.cs` 第 331 行），因此**不会**触发 `OnChannelStopped`。该事件恰好在「由运行转为停止」这一次转变上触发。

## 说明

- `Start` 首次使用时会创建通道，所以对一个没有任何注册的通道名调用 `TickManager.Start("demo")` 是合法的 —— 只是得到一个空的循环。
- 通道的线程名是 `VeloxDev.Update[<名字>]` 与 `VeloxDev.FixedUpdate[<名字>]`（`TickManager.cs` 第 310、316 行）。它们会出现在调试器的线程列表，以及演示的日志读数里。
