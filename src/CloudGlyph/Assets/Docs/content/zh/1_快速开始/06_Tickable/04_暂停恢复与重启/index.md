# 暂停、恢复与重启

暂停不是循环轮询的标志位。它是通道**时间源**的属性，两条泵 park 在它上面。正是这个决定让暂停中的通道零开销，也让一次 `Pause` 同时冻结帧循环和锚定在同一时钟上的动画。

## 1. 暂停是 bus 操作

`TickManager.cs` 第 386-404 行：

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

两者在不会改变任何东西时都是带保护的 no-op。

在泵内部，暂停表现为 park 而不是轮询：

```csharp
// TickManager.cs 第 522-526 行，UpdateLoop 内
if (!_bus.IsAdvancing)
{
    _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
    continue;
}
```

循环等待的谓词是 `IsAdvancing`，不是 `IsPaused`，因为时间速率为 `0` 也会停住时钟但不构成暂停。只检查 `IsPaused` 的循环会在冻结的时钟上空转。

**预期结果：** 调用 `TickManager.Pause("demo")` 后，`TickManager.IsPaused("demo")` 为 `true`，`TickManager.SystemStatus("demo")` 为 `"Paused"`，且 `TickManager.TotalFrames("demo")` 停止增长。调用返回后**可能还有一帧在途**落地 —— 像测试那样从暂停之后的一刻开始测量：

```csharp
TickManager.Pause(channel);
await Task.Delay(60);   // 让在途的一帧落地
var whilePaused = TickManager.TotalFrames(channel);
await Task.Delay(200);
// whilePaused == TickManager.TotalFrames(channel)
```

## 2. park 住的循环仍然活着

暂停期间 `IsUpdateThreadAlive` 与 `IsFixedUpdateThreadAlive` 返回 `true`。park 住的泵按定义没有活动，所以存活查询限定的是时钟而不是活动（`TickManager.cs` 第 195-199 行）。见 `03_配置并运行循环`。

**预期结果：** 当 `IsPaused("demo")` 为 `true` 时，两个存活查询都返回 `true`。

## 3. TogglePause

```csharp
TickManager.TogglePause("demo");
```

**预期结果：** 翻转暂停状态 —— 通道在运行且未暂停时调用 `Pause()`，否则调用 `Resume()`。对已停止的通道是 no-op，因为两个分支都被各自的保护挡下（`TickManager.cs` 第 444 行）。

## 4. StopAsync

```csharp
await TickManager.StopAsync("demo");
```

**预期结果：** `IsRunning("demo")` 变为 `false`，`SystemStatus("demo")` 变为 `"Stopped"`，两个存活查询变为 `false`，并触发 `OnChannelStopped`。

`StopAsync` 另有三件值得知道的事：

- **它会清掉暂停。** 下行途中调用 `_bus.Resume()`（`TickManager.cs` 第 341 行），所以暂停中被停止的通道回来后仍可运行（`TickableBusTests.StartingAChannelClearsAPauseLeftOverFromTheLastLifecycle`）。
- **它重置统计并排空队列**，在 `finally` 块中（第 365-373 行）。`TotalFrames`、`TotalTime` 与 `CurrentFPS` 归零。
- **它最多等两条泵 1 秒**，随后无论如何清空线程与任务字段。从 UI 的 `Closing` 处理器里 `await` 它是安全的；示例没有等，因为进程马上就要结束（`MainWindow.xaml.cs` 第 55-61 行）。

暂停中停止可用且不会挂起：park 住的泵等待的调用会观察取消令牌，所以 `StopAsync` 的取消能穿透进 park（`TickableBusTests.StoppingWhilePausedEndsTheChannel`）。

**注册在停止后仍然存在。** `finally` 块清的是四个队列，不是 `_behaviors`；已经排空过的注册在下次 `Start` 后会继续被驱动。停止时仍在队列里的注册会被丢弃，`_removeQueue` 里待处理的注销同样如此。存活的行为不会重跑 `Awake` / `Start`。

## 5. RestartAsync

```csharp
await TickManager.RestartAsync("demo");
```

**预期结果：** `IsRunning("demo")` 重新为 `true`，`TotalFrames("demo")` 很小（统计已重置），且 `Awake` / `Start` **不会**重跑。

最后一点是整个生命周期里最鲜明的区别：

| 操作 | 重跑 `Awake` / `Start`？ | 计数器重置？ |
|---|---|---|
| `StopAsync` 后 `Start` | 否 | 是 |
| `RestartAsync` | 否 | 是 |
| `CloseTickable()` 后 `InitializeTickable()` | **是** | 否 |

重新注册会为同一对象构建新的 wrapper，排空过程会在它上面调用 `InvokeAwake` 与 `InvokeStart`。停止再启动只会移动两条泵。WPF 示例把两组按钮都暴露出来（`MainWindow.xaml.cs` 第 105-119 行），正是为了让这个区别可见。

`RestartAsync` 就是 `StopAsync` 加两次等待再加 `Start`（`TickManager.cs` 第 408-432 行）：先最多等 1 秒确认关闭（若泵不肯停则回退到 `ForceCleanup`），再最多等 500 ms 让队列排空，然后启动。

**预期结果：** 重启后时钟重新锚定 —— 紧随重启送达的一帧其 `DeltaTime` 是一个帧间隔，而不是整段停机时间（`TickableBusTests.RestartingAChannelRePrimesItsClocks`）。

## 说明

- `Pause`、`Resume`、`TogglePause` 与 `Start` 是同步的；只有 `StopAsync` 与 `RestartAsync` 返回 `Task`。
- 速率 `0` 不是暂停：`IsPaused` 保持 `false`，`Resume` 抬不动它，只有 `SetTimeScale(<非零>)` 能让时钟重新走。
