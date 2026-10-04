# 04 · 暂停、恢复与重启

暂停不是循环去轮询的一个标志位，而是通道**时间源**的一个属性，两个泵 park 在它上面。这一个决定同时带来了两件事：暂停中的通道零开销，以及一次 `Pause` 能同时冻结帧循环与锚定到同一时钟上的动画。

## 1. 暂停是一次总线操作

`TickManager.cs` 第 384-402 行：

```csharp
public void Pause()
{
    if (!_isRunning || _bus.IsPaused) return;
    _bus.Pause();
    Paused?.Invoke(this, EventArgs.Empty);
}

public void Resume()
{
    if (!_isRunning || !_bus.IsPaused) return;
    _bus.Resume();
    Resumed?.Invoke(this, EventArgs.Empty);
}
```

两者在「什么都不会改变」时都是带保护的 no-op：对已停止或已暂停的通道调用 `Pause` 什么都不做、也不触发事件；对未暂停的通道调用 `Resume` 同理。

在泵内部，暂停表现为一次 park，而不是轮询：

```csharp
// TickManager.cs 第 520-524 行，位于 UpdateLoop 内
if (!_bus.IsAdvancing)
{
    _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
    continue;
}
```

泵等待的判据是 `IsAdvancing` 而**不是** `IsPaused`，因为速率为 `0` 也会停住时钟却不构成暂停。只检查 `IsPaused` 的循环会在冻结的时钟上空转。

**预期结果：** 调用 `TickManager.Pause("demo")` 后，`TickManager.IsPaused("demo")` 为 `true`，`TickManager.SystemStatus("demo")` 为 `"Paused"`，且 `TickManager.TotalFrames("demo")` 不再增长。调用返回后**可能还会落下一帧已在途的帧** —— 请从暂停之后的一个时刻开始读数，演示的测试就是这么做的：

```csharp
TickManager.Pause(channel);
await Task.Delay(60);   // 让已在途的一帧落完，之后的读数才是暂停期间的
var whilePaused = TickManager.TotalFrames(channel);
await Task.Delay(200);
// whilePaused == TickManager.TotalFrames(channel)
```

## 2. park 住的泵是活着的

暂停期间 `IsUpdateThreadAlive` 与 `IsFixedUpdateThreadAlive` 都返回 `true`。这是刻意的，也是「最近有没有活动」这个判据唯一需要修正的地方：park 住的泵按定义就没有活动。参见 `03_运行与配置循环`。

**预期结果：** 当 `IsPaused("demo")` 为 `true` 时，`IsUpdateThreadAlive("demo")` 与 `IsFixedUpdateThreadAlive("demo")` 均为 `true`。

## 3. TogglePause

```csharp
TickManager.TogglePause("demo");
```

**预期结果：** 切换暂停状态 —— 运行中且未暂停则 `Pause()`，否则 `Resume()`。对已停止的通道是 no-op，因为两个分支都会被各自的保护挡下。

## 4. StopAsync

```csharp
await TickManager.StopAsync("demo");
```

**预期结果：** `IsRunning("demo")` 变为 `false`，`SystemStatus("demo")` 变为 `"Stopped"`，两个存活查询都变为 `false`，并触发 `OnChannelStopped`。

`StopAsync` 还做了三件值得知道的事：

- **它会清掉暂停。** 下行过程中调用了 `_bus.Resume()`（第 339 行），所以「暂停中被停止」的通道重新可用。没有这一句，它重启后会立刻又 park 住再也跑不起来（`TickableBusTests.StartingAChannelClearsAPauseLeftOverFromTheLastLifecycle`）。
- **它在 `finally` 里重置统计并清空队列**（第 363-371 行）。`TotalFrames`、`TotalTime` 与 `CurrentFPS` 全部归零。
- **它等待两个泵的上限是 1 秒**，超时后仍会把线程与任务字段置空。在 UI 的 `Closing` 处理器里 `await` 它是安全的；演示没有 await，因为进程本来就要结束了（`MainWindow.xaml.cs` 第 69 行）。

暂停中停止必须能正常返回而不能挂住：park 住的泵等待的那个调用会观察取消令牌，所以 `StopAsync` 的取消能穿透进 park。`TickableBusTests.StoppingWhilePausedEndsTheChannel` 断言该任务能跑赢一个 5 秒的超时。

## 5. RestartAsync

```csharp
await TickManager.RestartAsync("demo");
```

**预期结果：** `IsRunning("demo")` 重新为 `true`，`TotalFrames("demo")` 是个小数字（统计被重置过），而 `Awake` / `Start` **不会**重新执行。

最后这一点是整个生命周期里最锋利的分界：

| 操作 | `Awake` / `Start` 再次执行？ | 计数器重置？ |
|---|---|---|
| `StopAsync` 后 `Start` | 否 | 是 |
| `RestartAsync` | 否 | 是 |
| `CloseTickable()` 后 `InitializeTickable()` | **是** | 否 |

重新注册会为同一个对象新建一个 wrapper，排空时对它调用 `InvokeAwake` 与 `InvokeStart`。停止再启动通道只是把泵挪了挪。WPF 演示同时提供了这两个按钮（`MainWindow.xaml.cs` 第 121-135 行），正是为了让这组对比可见。

`RestartAsync` 就是 `StopAsync` 加两次等待再加 `Start`（`TickManager.cs` 第 404-428 行）：先等最多 1 秒的关闭确认（确认不了就走 `ForceCleanup`），再等最多 500 ms 让队列排空，然后启动。

**预期结果：** 重启后时钟被重新锚定 —— 紧接重启送达的那一帧，其 `DeltaTime` 是一帧，而不是整段停机时间。

## 说明

- `Pause`、`Resume`、`TogglePause` 与 `Start` 都是同步的；只有 `StopAsync` 与 `RestartAsync` 返回 `Task`。
- 速率为 `0` 不是暂停：`IsPaused` 保持 `false`，`Resume` 抬不动它，只有 `SetTimeScale(<非零>)` 能让时钟重新走。
