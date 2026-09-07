# MonoBehaviour — 运行与配置循环

所有控制都经由静态类 `VeloxDev.TimeLine.MonoBehaviourManager`。每个方法都带可选的 `channel` 参数，默认是 `"default"` 通道；通道在配置、注册或生命周期调用首次命名它时惰性创建。行为、配置与生命周期都按通道划分。

## 1. 配置旋钮

按通道的设置作为变更请求入队，并在下一帧开始时应用（`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourManager.cs`）。

```csharp
MonoBehaviourManager.SetTargetFPS(60, "game");            // 合法 1..1000；越界被忽略
MonoBehaviourManager.SetFixedUpdateInterval(16, "game");  // 毫秒，合法 1..1000；越界被忽略
MonoBehaviourManager.SetTimeScale(1.0f, "game");          // 钳位到 0..10
MonoBehaviourManager.ExecuteOnMainThread(() => DoUiWork(), "game"); // 在下一个更新帧的帧首运行
```

- `SetTargetFPS` 为 Update 泵定速（默认 60）。
- `SetFixedUpdateInterval` 设定 FixedUpdate 泵的固定步长周期（毫秒，默认 16）。
- `SetTimeScale` 缩放该帧每个行为的 `FrameEventArgs.DeltaTime`（`0` 冻结 delta time，但不停止泵）。
- `ExecuteOnMainThread` 把一个 `Action` 入队，由 Update 泵在其下一帧的帧首运行 —— 它在*循环*线程上运行，而不是任何 UI 线程。

**预期结果：** 配置在下一个帧边界生效；状态查询一旦应用即可反映新值。

## 2. 线程或异步循环模式

通道的两个泵各自要么运行在后台 `Thread` 上（线程名为 `VeloxDev.Update[channel]` / `VeloxDev.FixedUpdate[channel]`），要么运行在 `async` 任务上。切换开关是 `MonoBehaviourManager.UseAsyncLoop`（全局），外加可选的按通道覆盖：

```csharp
MonoBehaviourManager.SetUseAsyncLoop(true, "game");   // 为该通道强制 async/await + Task.Delay
MonoBehaviourManager.ClearUseAsyncLoopOverride("game");
```

默认值与环境相关（`MonoBehaviourManager.cs`）：在 .NET 5+ 上 `UseAsyncLoop` 默认等于 `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()` —— 于是 WASM 与 iOS NativeAOT 走异步路径（无 `System.Threading.Thread`），而桌面 .NET 5+ 使用原生线程。较老目标（netstandard2.0 / netcoreapp3.0 / .NET Framework）上该属性默认为 `true`。当通道已在运行时设置覆盖会抛 `InvalidOperationException`；请在 `Start` 之前设置（[验证与完整代码](../06_验证与完整代码/)页的测试固定了这条）。

**预期结果：** `IsUpdateThreadAlive("game")` / `IsFixedUpdateThreadAlive("game")` 无论由哪种机制驱动，都报告对应泵是否在活跃跳动。

## 3. 启动与停止

```csharp
var counter = new FrameCounter();        // 在构造函数中注册（入队）
MonoBehaviourManager.Start("game");      // 立即返回；首帧清空加入队列
// Awake() 与 Start() 在此于循环线程上触发。
await MonoBehaviourManager.StopAsync("game");
```

`Start` 启动两个泵、重建行为列表并触发 `OnChannelStarted`；它在首帧之前返回，因此入队行为的 `Awake` / `Start` 钩子会稍后在循环线程上运行。`StopAsync` 取消两个泵（1 秒关闭超时）、重置通道统计（`CurrentFPS`、`TotalFrames`、`TotalTime` 等）、清空挂起的加入/移除/配置/主线程队列并触发 `OnChannelStopped`。已注册的行为会被保留 —— 它们只会在同一通道下一次 `Start` 时重新变活跃（不会再次触发 `Awake` / `Start`）。

**预期结果：** `Start` 之后不久 `SystemStatus("game")` 返回 `"Running"`；`StopAsync` 之后返回 `"Stopped"`。

## 4. 状态查询

```csharp
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));        // "Running" | "Paused" | "Stopped"
Console.WriteLine(MonoBehaviourManager.IsRunning("game"));
Console.WriteLine(MonoBehaviourManager.IsPaused("game"));
Console.WriteLine(MonoBehaviourManager.CurrentFPS("game"));          // 实测值，约每秒更新一次
Console.WriteLine(MonoBehaviourManager.TargetFPS("game"));
Console.WriteLine(MonoBehaviourManager.ActiveBehaviorCount("game"));
Console.WriteLine(MonoBehaviourManager.TotalFrames("game"));
Console.WriteLine(MonoBehaviourManager.TotalTimeMs("game"));
```

对尚未创建的通道，查询返回中性默认值（`0` / `"Stopped"` / 默认目标 FPS）。`ChannelNames` 枚举目前创建过的所有通道。

**预期结果：** 循环运行期间 `IsRunning` 为 `true`，`CurrentFPS` 追踪实测帧率，`ActiveBehaviorCount` 等于通道已拾取的行为数。

## 5. 通道事件

管理器暴露四个静态事件；每个事件都在调用生命周期方法的线程上同步触发，载荷为携带 `ChannelName` 的 `MonoBehaviourChannelEventArgs`：

```csharp
MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine($"[OnChannelStarted] {e.ChannelName}");
MonoBehaviourManager.OnChannelPaused  += (s, e) => Console.WriteLine($"[OnChannelPaused]  {e.ChannelName}");
MonoBehaviourManager.OnChannelResumed += (s, e) => Console.WriteLine($"[OnChannelResumed] {e.ChannelName}");
MonoBehaviourManager.OnChannelStopped += (s, e) => Console.WriteLine($"[OnChannelStopped] {e.ChannelName}");
```

因此 `RestartAsync` 会先触发 `OnChannelStopped` 再触发 `OnChannelStarted`。

**预期结果：** 在 `Start` 前订阅即可在每个生命周期转换时打印一条事件。

## 6. 循环内部的取消与错误处理

- 每个泵持有一个 `CancellationTokenSource`；`StopAsync` 会取消它，泵把取消当作正常退出（没有异常逃逸出循环）。
- 行为钩子内部抛出的异常会被通道捕获（经 `Debug.WriteLine` 记录；无调试器的 Release 为空操作），不会停止循环；异常按 wrapper 吞掉，该帧剩余行为照常运行。
- `FrameEventArgs.DeltaTime` 反映经 `TimeScale` 缩放的真实流逝时间；`TimeScale` 为 `0` 时该帧 `DeltaTime` 为零。

**预期结果：** 钩子抛一次异常不会杀死通道；停止循环会在关闭超时内汇合两个泵，并把通道留在 `"Stopped"`。

## 运行声明

- ⚠️ 仅静态核验 —— 本页的方法名、默认值与钳位转录自 `MonoBehaviourManager.cs`；本页代码没有单独编译。相同的调用在[验证与完整代码](../06_验证与完整代码/)页的程序中被端到端演练。
