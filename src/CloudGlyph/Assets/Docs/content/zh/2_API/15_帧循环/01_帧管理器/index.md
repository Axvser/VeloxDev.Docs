# 帧管理器

所有通道的静态所有者：线程、帧率、固定步长、时间缩放与已注册行为。命名空间 `VeloxDev.TimeLine`。

## VeloxDev.TimeLine

### 类：TickManager

**签名：** `public static class TickManager`

**常量**

| 成员 | 类型 | 值 |
|---|---|---|
| `DEFAULT_CHANNEL` | `const string` | `"default"` |

**属性**

| 成员 | 类型 | 说明 |
|---|---|---|
| `UseAsyncLoop` | `static bool { get; set; }` | 用 `async` / `Task.Delay` 替代原生线程。浏览器与 iOS 上默认 `true`；其余由 `#if NET5_0_OR_GREATER` 按平台决定。 |
| `ChannelNames` | `static IEnumerable<string> { get; }` | 所有已创建通道的名称。 |

**事件**

| 成员 | 签名 | 说明 |
|---|---|---|
| `OnChannelStarted` | `static event EventHandler<TickChannelEventArgs>?` | 通道启动。 |
| `OnChannelPaused` | `static event EventHandler<TickChannelEventArgs>?` | 通道暂停。 |
| `OnChannelResumed` | `static event EventHandler<TickChannelEventArgs>?` | 通道恢复。 |
| `OnChannelStopped` | `static event EventHandler<TickChannelEventArgs>?` | 通道停止。 |
| `OnBehaviorError` | `static event EventHandler<TickBehaviorErrorEventArgs>?` | 行为或主线程动作抛出异常。循环继续运行；无订阅者时错误只写入 `Debug`。 |

**生命周期**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Start` | `static void Start(string channel = DEFAULT_CHANNEL)` | 启动或恢复通道。运行中幂等。 |
| `StopAsync` | `static Task StopAsync(string channel = DEFAULT_CHANNEL)` | 停止通道、汇合循环并重置统计。 |
| `Pause` | `static void Pause(string channel = DEFAULT_CHANNEL)` | 冻结时钟与两个循环。 |
| `Resume` | `static void Resume(string channel = DEFAULT_CHANNEL)` | 以最后设置的速率恢复。 |
| `RestartAsync` | `static Task RestartAsync(string channel = DEFAULT_CHANNEL)` | 停止、等待关闭，再启动。 |
| `TogglePause` | `static void TogglePause(string channel = DEFAULT_CHANNEL)` | 运行时暂停，暂停时恢复。 |
| `RegisterBehaviour` | `static void RegisterBehaviour(ITickable behavior, string channel = DEFAULT_CHANNEL)` | 入队一个行为；`Awake` 与 `Start` 在通道下次排空时运行。 |
| `UnregisterBehaviour` | `static void UnregisterBehaviour(ITickable behavior, string channel = DEFAULT_CHANNEL)` | 入队取消注册。 |

**配置**

| 成员 | 签名 | 说明 |
|---|---|---|
| `SetTargetFPS` | `static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)` | 超出 1–1000 的值被忽略。 |
| `SetFixedUpdateInterval` | `static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)` | 固定步长（毫秒）；超出 1–1000 的值被忽略。 |
| `SetTimeScale` | `static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)` | 乘以流逝时间。`0` 冻结但不置 `IsPaused`；负值抛 `ArgumentOutOfRangeException`。 |
| `ExecuteOnMainThread` | `static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)` | 把工作入队到通道更新线程。 |
| `SetUseAsyncLoop` | `static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)` | 逐通道覆盖。通道运行中抛 `InvalidOperationException`。 |
| `ClearUseAsyncLoopOverride` | `static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)` | 移除逐通道覆盖。运行中抛 `InvalidOperationException`。 |

**状态查询**

| 成员 | 签名 | 说明 |
|---|---|---|
| `IsRunning` | `static bool IsRunning(string channel = DEFAULT_CHANNEL)` | 通道存在且运行中。 |
| `IsPaused` | `static bool IsPaused(string channel = DEFAULT_CHANNEL)` | 时钟已暂停。速率为零不算暂停。 |
| `CurrentFPS` | `static int CurrentFPS(string channel = DEFAULT_CHANNEL)` | 实测每秒帧数。 |
| `TargetFPS` | `static int TargetFPS(string channel = DEFAULT_CHANNEL)` | 请求的每秒帧数；未知通道为 `60`。 |
| `TotalTime` | `static TimeSpan TotalTime(string channel = DEFAULT_CHANNEL)` | 时钟启动以来的虚拟时间。 |
| `TotalTimeMs` | `static long TotalTimeMs(string channel = DEFAULT_CHANNEL)` | `TotalTime` 的毫秒值。 |
| `TotalFrames` | `static long TotalFrames(string channel = DEFAULT_CHANNEL)` | 已产出帧数。 |
| `ActiveBehaviorCount` | `static int ActiveBehaviorCount(string channel = DEFAULT_CHANNEL)` | 已注册行为数。 |
| `TimeScale` | `static float TimeScale(string channel = DEFAULT_CHANNEL)` | 当前速率；未知通道为 `1`。 |
| `Bus` | `static ITimeSourceControl? Bus(string channel = DEFAULT_CHANNEL)` | 通道传输，通道不存在时为 `null`。把它传给动画的 `Execute(target, timeline)` 重载，使一次暂停与一个速率同时移动帧和动画。 |
| `SystemStatus` | `static string SystemStatus(string channel = DEFAULT_CHANNEL)` | `"Stopped"`、`"Paused"` 或 `"Running"`。 |
| `IsUpdateThreadAlive` | `static bool IsUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | 更新循环的线程/任务存活。 |
| `IsFixedUpdateThreadAlive` | `static bool IsFixedUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | 固定更新循环的线程/任务存活。 |

### 类：TickChannelEventArgs

**签名：** `public sealed class TickChannelEventArgs(string channelName) : EventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `ChannelName` | `string { get; }` | 事件所属通道。 |

### 类：TickBehaviorErrorEventArgs

**签名：** `public sealed class TickBehaviorErrorEventArgs(string channelName, string stage, Exception exception) : EventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `ChannelName` | `string { get; }` | 发生错误的通道。 |
| `Stage` | `string { get; }` | `Awake`、`Start`、`Update`、`LateUpdate`、`FixedUpdate` 或 `MainThread`。 |
| `Exception` | `Exception { get; }` | 抛出的异常。 |

## 行为说明

- 每个通道拥有两个循环（更新、固定更新）、自己的目标 FPS、固定步长与时间缩放。一个通道上的行为绝不会在另一通道的线程上运行。
- 行为按注册顺序依次运行。抛异常的行为经 `OnBehaviorError` 报告，不停止循环。
- `Update` 与 `LateUpdate` 共用同一个 `FrameEventArgs`；在 `Update` 中置 `Handled` 会跳过该帧剩余的 `Update` 行为与全部 `LateUpdate` 行为。`FixedUpdate` 每步创建自己的参数，不受影响。
- 停滞后 `FixedUpdate` 补还欠下的步：一次唤醒可能产生多次调用，`TotalTime` 连续递增。
- `SetTimeScale(0)` 冻结时钟，但 `IsPaused` 仍为 false、`SystemStatus` 仍为 `"Running"`。只有非零速率能让它重新前进。

## 示例

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

await Task.Delay(400);
Console.WriteLine($"running={TickManager.IsRunning("quickstart")} frames={TickManager.TotalFrames("quickstart")}");

TickManager.SetTargetFPS(30, "quickstart");
TickManager.SetTimeScale(0.5f, "quickstart");
var bus = TickManager.Bus("quickstart");

await TickManager.StopAsync("quickstart");
ticker.CloseTickable();
```

类形状见[帧驱动契约](../00_帧驱动契约/index.md)，完整程序见[快速开始](../../../1_快速开始/15_帧循环/index.md)。
