# MonoBehaviour — 暂停恢复与重启

除 `Start` / `StopAsync` 之外（见[运行与配置循环](../03_运行与配置循环/)页），生命周期控制还有三个方法加一个切换，全部按通道进行。

## 1. 暂停

`Pause` 冻结该通道的时间源，两个泵随即 park 在它上面。期间不再派发任何 `Update`、`LateUpdate` 或 `FixedUpdate`，时间也不再累计，而且在 `Resume` 之前两个泵**一次唤醒都不产生**。由于是时钟停住而不是仅仅跳过回调，暂停的那一段永远不会进入 `TotalTime`，也不会算在锚到同一时间源的动画头上：

```csharp
MonoBehaviourManager.Pause("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Paused"
Console.WriteLine(MonoBehaviourManager.IsPaused("game"));       // True
```

**预期结果：** 暂停期间行为计数器停止增长，`TotalFrames` / `TotalTime` 冻结。

## 2. 恢复

`Resume` 清掉暂停标志，两个泵从停下的地方继续：

```csharp
MonoBehaviourManager.Resume("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Running"
```

**预期结果：** `Resume` 之后状态回到 `"Running"`，帧派发恢复。

## 3. 切换暂停

`TogglePause` 翻转当前状态：已暂停则恢复，否则暂停。

```csharp
MonoBehaviourManager.TogglePause("game");
```

**预期结果：** 反复调用会让 `SystemStatus` 在 `"Paused"` 与 `"Running"` 之间交替。

## 4. 重启

`RestartAsync` 在同一个通道上先干净地停止、再全新启动：它取消并汇合两个泵（1 秒关闭超时，超时则强制清理），等待挂起的加入/移除/配置队列排空（500 ms 预算），然后再次调用 `Start`。沿途会触发 `OnChannelStopped` 再触发 `OnChannelStarted`：

```csharp
await MonoBehaviourManager.RestartAsync("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Running"
```

**预期结果：** `RestartAsync` 之后通道回到 `"Running"`，其统计被重置（`TotalFrames` 从接近零重新开始），已注册的行为仍然活跃 —— 但它们的 `Awake` / `Start` 钩子不会被第二次调用，因为循环只在行为首次从加入队列被拾取时才调用它们。

## 5. 在一个可观察窗口内暂停 / 恢复

[验证与完整代码](../06_验证与完整代码/)页的完整程序在暂停期间对计数器采样两次，以证明没有前进：

```csharp
MonoBehaviourManager.Pause("game");
long a = Volatile.Read(ref counter.UpdateCount);
await Task.Delay(300);
long b = Volatile.Read(ref counter.UpdateCount);
Console.WriteLine($"Updates grew while paused: {b - a}");   // 0

MonoBehaviourManager.Resume("game");
```

**预期结果：** 暂停期间打印的增长为 `0`，恢复后重新为正。

## 运行声明

- ⚠️ 仅静态核验 —— 本页的暂停/窗口、恢复与重启行为转录自 `MonoBehaviourManager.cs` 中的循环体；它在[验证与完整代码](../06_验证与完整代码/)页被一次记录下的运行端到端演练。
