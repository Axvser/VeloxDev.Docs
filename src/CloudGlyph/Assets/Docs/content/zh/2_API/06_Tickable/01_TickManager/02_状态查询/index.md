# `TickManager` — 状态查询

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 1105-1156 行。

十三个成员全部接受 `string channel = TickManager.DEFAULT_CHANNEL`，全部是 `static`，全部可从任意线程调用。它们的共同契约值得只说一次：

> 查询永不创建通道，也永不抛异常。当具名通道不存在时，它返回「已停止」的答案 —— `false`、`0`、`TimeSpan.Zero`、`"Stopped"`，`Bus` 则为 `null`。

每一个的实现都是 `_channels.TryGetValue(channel, out var c) ? c.X : <回退值>`。

| 成员 | 签名 | 通道存在时返回 | 不存在时返回 |
|---|---|---|---|
| `IsRunning` | `public static bool IsRunning(string channel = DEFAULT_CHANNEL)` | `_isRunning` —— 泵已启动且未停止 | `false` |
| `IsPaused` | `public static bool IsPaused(string channel = DEFAULT_CHANNEL)` | `_bus.IsPaused` | `false` |
| `CurrentFPS` | `public static int CurrentFPS(string channel = DEFAULT_CHANNEL)` | 实测帧率，每墙钟秒刷新一次 | `0` |
| `TargetFPS` | `public static int TargetFPS(string channel = DEFAULT_CHANNEL)` | 配置的目标帧率 | `60`（`DEFAULT_TARGET_FPS`） |
| `TotalTime` | `public static TimeSpan TotalTime(string channel = DEFAULT_CHANNEL)` | `Start` 以来的虚拟时间 | `TimeSpan.Zero` |
| `TotalTimeMs` | `public static long TotalTimeMs(string channel = DEFAULT_CHANNEL)` | `(long)TotalTime.TotalMilliseconds` | `0` |
| `TotalFrames` | `public static long TotalFrames(string channel = DEFAULT_CHANNEL)` | `Start` 以来完成的帧数 | `0` |
| `ActiveBehaviorCount` | `public static int ActiveBehaviorCount(string channel = DEFAULT_CHANNEL)` | 行为字典的大小 | `0` |
| `TimeScale` | `public static float TimeScale(string channel = DEFAULT_CHANNEL)` | 时钟速率 | `1.0f`（`DEFAULT_TIME_SCALE`） |
| `SystemStatus` | `public static string SystemStatus(string channel = DEFAULT_CHANNEL)` | `"Stopped"` / `"Paused"` / `"Running"` | `"Stopped"` |
| `IsUpdateThreadAlive` | `public static bool IsUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | 见下 | `false` |
| `IsFixedUpdateThreadAlive` | `public static bool IsFixedUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | 见下 | `false` |
| `Bus` | `public static ITimeSourceControl? Bus(string channel = DEFAULT_CHANNEL)` | 通道的时间源 | `null` |

#### `TickManager.SystemStatus`

**签名：**
`public static string SystemStatus(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** 三个字面量之一 —— `!_isRunning` 时为 `"Stopped"`，总线暂停时为 `"Paused"`，其余为 `"Running"`（第 185 行）。

**说明：**
- 这些字符串就是公开契约；没有对应枚举。
- **速率为 `0` 时仍报 `"Running"`。** 冻结的时钟不是暂停，这是该查询唯一覆盖不到的状态。「时钟到底在不在走」请用 `TickManager.Bus(channel)?.IsAdvancing` —— WPF 演示把两者并排打印正是为此（`MainWindow.xaml.cs` 第 307-324 行）。

#### `TickManager.IsUpdateThreadAlive` / `TickManager.IsFixedUpdateThreadAlive`

**签名：**
`public static bool IsUpdateThreadAlive(string channel = TickManager.DEFAULT_CHANNEL)`
`public static bool IsFixedUpdateThreadAlive(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `bool` —— 泵在运行期间为 `true`，包括它 park 住的时候。

**说明：**
- 实现（第 193-197 行）并不是一个活跃度测试：

```csharp
public bool IsUpdateThreadAlive => _isRunning && _isUpdateThreadActive &&
    (!_bus.IsAdvancing || IsRecentActivity(Interlocked.Read(ref _updateThreadLastActivityTimestamp)));
```

  其中 `!_bus.IsAdvancing ||` 这一项正是阻止「暂停中的通道被报成线程已死」的关键：park 住的泵按定义没有活动，否则 2 秒（`THREAD_INACTIVITY_TIMEOUT_MS`）窗口必然过期。
- `IsRecentActivity` 对时间戳 `0` 也返回 `false`，那是启动后、泵第一次迭代之前的状态。

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs（第 151-155 行）
// 旧实现靠每 10ms 醒来轮询暂停标志，暂停中的循环仍然活着；这里改为 park 在总线上，
// 所以「线程还活着吗」不能再用「最近有没有活动」来判断。
Assert.IsTrue(TickManager.IsUpdateThreadAlive(channel),
    "a parked loop is alive, not dead — the liveness query has to account for the stalled clock");
Assert.IsTrue(TickManager.IsFixedUpdateThreadAlive(channel));
```

#### `TickManager.Bus`

**签名：**
`public static ITimeSourceControl? Bus(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `ITimeSourceControl?` —— 通道的时间源；通道从未创建时为 `null`。

**异常：** 无。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 307 行）
var bus = TickManager.Bus(DemoChannel.Name);
$"IsAdvancing {bus?.IsAdvancing}  IsPaused {bus?.IsPaused}  Epoch {bus?.Epoch}  Rate {bus?.Rate ?? 0:F2}×"
```

**说明：**
- `null` 是「查询不该顺手创建通道」这一决定的诚实答案（`TickableBusTests.BusIsNullForAChannelThatWasNeverStarted`）。
- 一个通道终生只有一个 transport；两次调用返回同一实例（`TickableBusTests.BusIsStableForAStartedChannel`）。
- 该时间源在通道构造时经 `TimerCore.CreateTimeSource<ITimeSourceControl>()` 解析一次（第 116 行），因此平台可以在那里注册自己的实现来替换。默认实现是 `VeloxDev.Timing` 下的 `TimeSourceCore`。
- 把它传给 `TransitionCore.Execute(target, timeline)`，就是「一次 `Pause()` 同时停掉帧回调与动画」「通道速率同时乘到两者上」的由来（`TickableBusTests.PausingAChannelStopsItsFramesAndTheAnimationAnchoredToIt`）。
- 消费者通常会用到的成员：`IsAdvancing`、`IsPaused`、`Rate`、`Position`、`Epoch`、`Pause()`、`Resume()`、`SetRate(double)`、`WaitWhileStalledAsync(CancellationToken)`。

#### `TickManager.ActiveBehaviorCount`

**签名：**
`public static int ActiveBehaviorCount(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `int` —— 通道行为字典中的条目数。

**说明：**
- 统计的是**已排空**的注册，不是已入队的：`RegisterBehaviour` 只在 update 泵处理该队列时才让它增加。同一帧内注册并查询，可能还统计不到。
- 同一实例注册两次只算一次 —— 字典以 `RuntimeHelpers.GetHashCode(behavior)` 为键。
- 计数只在 `UnregisterBehaviour` 也被排空之后才下降。
