# `TickManager` — 生命周期与注册

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 1046-1071 行（静态包装）与第 274-441 行（`LoopChannel` 实现）。

这里的每个成员都接受 `string channel = TickManager.DEFAULT_CHANNEL`，并转发到该通道 `LoopChannel` 上的同名成员。全部经由 `GetOrCreateChannel` **在首次使用时创建通道**。`StopAsync` 对从未启动的通道返回已完成的任务。

#### `TickManager.Start`

**签名：**
`public static void Start(string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channel` | `string` | 要创建（如需要）并启动的通道 |

**返回：** `void`。

**异常：** 无。对已在运行的通道再次启动是 no-op —— `LoopChannel.Start` 第一句就是 `if (_isRunning) return;`（第 276 行）。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 60 行）
TickManager.Start(DemoChannel.Name);
```

**说明：**
- 启动 update 与 fixed-update 两条线程（`VeloxDev.Update[<通道名>]`、`VeloxDev.FixedUpdate[<通道名>]`，`ThreadPriority.AboveNormal`，`IsBackground = true`）；当 `EffectiveUseAsyncLoop` 为真时改为启动两个异步循环。
- 把两个采样器重新锚定到「现在」（第 288-289 行），并调用 `_bus.Resume()`（第 293 行），因此上一个生命周期遗留的暂停不会带过来。
- 重建按执行顺序排序的行为缓存数组，然后触发 `Started` → `OnChannelStarted`。

#### `TickManager.StopAsync`

**签名：**
`public static Task StopAsync(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `Task` —— 在两个泵停止、队列清空、统计重置后完成。

**异常：** 无可观察的异常。泵的 join 包在 `try { … } catch (Exception) { }` 里，清理放在 `finally`，所以返回的 task 不会 fault。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 69 行）
_ = TickManager.StopAsync(DemoChannel.Name);
```

**说明：**
- 若通道未运行则立即返回，且在这种情况下**不**触发 `OnChannelStopped`。
- 取消两个泵，然后最多等 `RESTART_SHUTDOWN_TIMEOUT_MS`（1 秒）。线程路径用 `Thread.Join`，异步路径用 `Task.WhenAny(Task.WhenAll(...), Task.Delay(1000))`。
- 下行途中清掉暂停（`_bus.Resume()`，第 339 行）—— 暂停中被停止的通道回来后是可运行的。它**不**会解除速率为 `0` 造成的冻结。
- 重置 `TotalTime`、`TotalFrames`、`CurrentFPS` 与配置缓存时间戳，并排空全部四个队列。
- 对 `Pause()` park 住的通道是安全的：park 会观察取消令牌，所以取消能穿透进去。

#### `TickManager.Pause`

**签名：**
`public static void Pause(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `void`。**异常：** 无。

**说明：**
- 通道未运行或已暂停时为 no-op（第 386 行）。
- 在通道的时间源上置 `IsPaused`，并触发 `Paused` → `OnChannelPaused`。
- 两个泵 park 在 `WaitWhileStalledAsync` 上而不是轮询，所以暂停中的通道完全不产生唤醒。
- 由于暂停状态属于共享的时间源，锚定在 `TickManager.Bus(channel)` 上的动画会在同一瞬间冻住。

#### `TickManager.Resume`

**签名：**
`public static void Resume(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `void`。**异常：** 无。

**说明：**
- 通道未运行或未暂停时为 no-op（第 399 行）。
- 触发 `Resumed` → `OnChannelResumed`。
- 在速率为 `0` 之后，它只解除暂停而不让时钟前进 —— 通道继续 park，直到速率被设为非零（`LoopChannel.Resume` 的备注，第 391-396 行）。

#### `TickManager.TogglePause`

**签名：**
`public static void TogglePause(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `void`。

**说明：**
- 实现是 `if (_bus.IsPaused) Resume(); else Pause();`（第 440 行），两个分支都继承上面的保护：对已停止的通道是 no-op。
- 触发 `OnChannelPaused` 或 `OnChannelResumed`，不会两者都触发。

#### `TickManager.RestartAsync`

**签名：**
`public static Task RestartAsync(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `Task` —— 通道停止、稳定并再次启动后完成。

**说明：**
- 先 `StopAsync`，再最多等 1 秒直到 `!_isRunning && !_isUpdateThreadActive && !_isFixedUpdateThreadActive`；超时则向 `Debug.WriteLine` 写 `Warning: Force restarting after timeout` 并调用 `ForceCleanup`。
- 然后最多等 500 ms 让四个队列排空（结果被忽略），最后 `Start()`。
- **不会**对已注册行为重跑 `Awake` / `Start`。只有 `CloseTickable()` + `InitializeTickable()` 会。

#### `TickManager.RegisterBehaviour`

**签名：**
`public static void RegisterBehaviour(ITickable behavior, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `behavior` | `ITickable` | 要添加的行为实例。`null` 被接受并忽略 |
| `channel` | `string` | 目标通道；不存在则创建 |

**返回：** `void`。

**异常：** 无。`null` 被 `if (behavior != null) _addQueue.Enqueue(behavior);`（第 432 行）滤掉。

**示例：**
```text
// 源码：生成的 InitializeTickable()（TickWriter.cs 第 83 行）
TickManager.RegisterBehaviour(this, "demo");
```

**说明：**
- 该调用只是入队。Update 泵在采样下一帧之前于 `ProcessAddedBehaviors`（第 785-801 行）排空队列，所以 `InvokeAwake()` 与 `InvokeStart()` 在 update 线程上、**在第一帧帧体之前**运行 —— 无论注册发生在 `Start` 之前还是之后。
- 行为以 `RuntimeHelpers.GetHashCode(behavior)` 为键，所以同一实例注册两次是替换而不是新增一个 wrapper —— 但仍会在替换品上再跑一遍 `InvokeAwake` / `InvokeStart`。
- 执行顺序即注册顺序：每个 wrapper 用 `Interlocked.Increment(ref _instanceCounter)` 作为 `ExecutionOrder`，缓存数组按它对它做插入排序。
- 注册不会立刻启动行为：若通道未运行，`Awake` / `Start` 要等到 `Start` 之后的第一帧。

#### `TickManager.UnregisterBehaviour`

**签名：**
`public static void UnregisterBehaviour(ITickable behavior, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `behavior` | `ITickable` | 要移除的实例。`null` 被接受并忽略 |
| `channel` | `string` | 它注册所在的通道 |

**返回：** `void`。**异常：** 无。

**示例：**
```text
// 源码：生成的 CloseTickable()（TickWriter.cs 第 88 行）
TickManager.UnregisterBehaviour(this, "demo");
```

**说明：**
- 入队；排空过程（`ProcessRemovedBehaviors`，第 803-816 行）移除 wrapper、清空它并归还 `_wrapperPool`。
- 移除是**静默的**：`UnregisterBehaviour` 只移除 wrapper，不对行为调用任何钩子 —— 循环从不调用「关闭」回调。（`ITickable` 上*确实*有 `CloseTickable()`，但它正是*执行*注销的那个方法，所以注销不会反过来调用它。）需要清理的资源由调用方自行处理。
- 移除后该实例仍然实现 `ITickable`，可以再次注册 —— 而再次注册会在新的 wrapper 上再跑一遍 `Awake` 与 `Start`。
