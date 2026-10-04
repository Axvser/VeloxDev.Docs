# `TickManager`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。一个覆盖多个具名循环通道的静态、线程安全门面。

```csharp
public static class TickManager
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs`（1163 行）。

`TickManager` 是本特性运行期的唯一公开入口。所有成员都是 `static`；除 `ChannelNames` 外，每个成员都带一个末位的 `string channel = DEFAULT_CHANNEL` 参数。通道由 `GetOrCreateChannel` 惰性创建，存在一个进程范围的 `ConcurrentDictionary<string, LoopChannel>`（`_channels`，第 1017 行）中 —— 因此该管理器是进程级全局状态，通道的生命周期长于任何注册在其上的行为。

## 哪些是公开的，哪些不是

| 公开 | 私有（不得出现在用户代码中） |
|---|---|
| 下面记录的 34 个静态成员 | 嵌套类型 `LoopChannel`、`BehaviorWrapper`、`ConfigChangeRequest`、`ObjectPool<T>` |
| `TickChannelEventArgs`（同文件中的独立顶层类型） | `GetOrCreateChannel`、`RebuildCachedWrappers`、`ProcessAddedBehaviors`、`ExecuteBehaviors*Sync`、`CreateFrameEventArgs`、`Sleep`、`ForceCleanup` 等 |

`LoopChannel` 是 `private sealed`（第 99 行）。两个泵、通道自己的时间源与通道自己的事件都住在里面，`TickManager` 之外没有任何东西能命名它。唯一公开通往通道时钟的门是 `TickManager.Bus`。

## 成员索引

| 分组 | 成员 | 页面 |
|---|---|---|
| 生命周期与注册 | `Start`、`StopAsync`、`Pause`、`Resume`、`TogglePause`、`RestartAsync`、`RegisterBehaviour`、`UnregisterBehaviour` | [生命周期](00_生命周期/index.md) |
| 配置 | `DEFAULT_CHANNEL`、`UseAsyncLoop`、`ChannelNames`、`SetTargetFPS`、`SetFixedUpdateInterval`、`SetTimeScale`、`ExecuteOnMainThread`、`SetUseAsyncLoop`、`ClearUseAsyncLoopOverride` | [配置](01_配置/index.md) |
| 状态查询 | `IsRunning`、`IsPaused`、`CurrentFPS`、`TargetFPS`、`TotalTime`、`TotalTimeMs`、`TotalFrames`、`ActiveBehaviorCount`、`TimeScale`、`SystemStatus`、`IsUpdateThreadAlive`、`IsFixedUpdateThreadAlive`、`Bus` | [状态查询](02_状态查询/index.md) |
| 事件 | `OnChannelStarted`、`OnChannelPaused`、`OnChannelResumed`、`OnChannelStopped` | [事件](03_事件/index.md) |

## 默认值与上限

这些常量是 `private`，但它们定义了公开行为，所以在此记录，而不是留给读者去发现：

| 常量 | 值 | 效果 |
|---|---|---|
| `DEFAULT_CHANNEL` | `"default"` | **公开。** 省略参数时使用的通道 |
| `DEFAULT_TARGET_FPS` | `60` | 新通道的初始目标帧率 |
| `MIN_FPS` / `MAX_FPS` | `1` / `1000` | `SetTargetFPS` 的接受范围；超出即忽略 |
| `DEFAULT_FIXED_UPDATE_INTERVAL_MS` | `16` | 初始 `FixedUpdate` 步长 |
| `MIN_UPDATE_INTERVAL_MS` / `MAX_UPDATE_INTERVAL_MS` | `1` / `1000` | `SetFixedUpdateInterval` 的接受范围；超出即忽略 |
| `DEFAULT_TIME_SCALE` | `1.0f` | 通道不存在时 `TimeScale` 的返回值 |
| `DEFAULT_OBJECT_POOL_SIZE` | `50` | 通道三个对象池各自的容量 |
| `MAX_CONFIG_CACHE_DURATION_MS` | `1000` | 排序后行为数组的缓存时长 |
| `THREAD_INACTIVITY_TIMEOUT_MS` | `2000` | 两个存活查询使用的活跃度窗口 |
| `RESTART_SHUTDOWN_TIMEOUT_MS` | `1000` | `StopAsync` / `RestartAsync` 等待两个泵的时长 |
| `RESTART_QUEUE_CLEAR_TIMEOUT_MS` | `500` | `RestartAsync` 等待队列排空的时长 |
| `MAX_SLEEP_CHUNK_MS` | `50` | 长睡眠按此分片，使停止能在此时间内被察觉 |
| `MIN_SLEEP_MS` | `1` | 时钟推进为零时的退避 |

源码：`TickManager.cs` 第 10-33 行。

## 位于本页边界上的其他类型

- **`TickChannelEventArgs`** —— 四个静态事件的载荷；单独记录（[TickChannelEventArgs](../05_TickChannelEventArgs/index.md)）。
- **`ITickable`** —— `RegisterBehaviour` 接受的类型；单独记录（[ITickable](../07_ITickable/index.md)）。
- **`ITimeSourceControl`**（`VeloxDev.Timing`）—— `Bus` 的返回类型。它属于共享基础设施，随过渡动画特性一并记录；本特性用户需要的成员是 `IsAdvancing`、`IsPaused`、`Rate`、`Position`、`Epoch`、`Pause()`、`Resume()`、`SetRate(double)` 与 `WaitWhileStalledAsync(CancellationToken)`。
