# MonoBehaviour — `MonoBehaviourManager`

命名空间 `VeloxDev.TimeLine`。一个静态、线程安全的门面，封装按名称划分的循环通道。省略 `channel` 实参时使用默认通道常量：`public const string DEFAULT_CHANNEL = "default";`

### 生命周期

#### `MonoBehaviourManager.Start`

**签名：**
`public static void Start(string channel = DEFAULT_CHANNEL)`

**返回：** `void`

**示例：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 218 行）
MonoBehaviourManager.Start();
```

**说明：**
- 首次使用会创建通道；启动 Update + FixedUpdate 线程（`UseAsyncLoop` 为 `true` 时改为异步任务）；触发 `OnChannelStarted`。

#### `MonoBehaviourManager.StopAsync`

**签名：**
`public static Task StopAsync(string channel = DEFAULT_CHANNEL)`

**返回：** `Task` — 在线程汇合（1 秒超时）、队列清空、统计重置后完成。

**示例：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 113 行）
await MonoBehaviourManager.StopAsync();
```

**说明：**
- 触发 `OnChannelStopped`；之后通道可重新启动。

#### `MonoBehaviourManager.Pause`

**签名：**
`public static void Pause(string channel = DEFAULT_CHANNEL)`

**返回：** `void`

**说明：**
- 通道未运行或已暂停时为无操作。暂停期间循环进入休眠；触发 `OnChannelPaused`。

#### `MonoBehaviourManager.Resume`

**签名：**
`public static void Resume(string channel = DEFAULT_CHANNEL)`

**返回：** `void`

**说明：**
- 未暂停时为无操作。触发 `OnChannelResumed`。

#### `MonoBehaviourManager.RestartAsync`

**签名：**
`public static Task RestartAsync(string channel = DEFAULT_CHANNEL)`

**返回：** `Task` — 在通道停止并重新启动后完成。

**说明：**
- 先停止，等待关闭确认（超过 1 秒强制清理），等待队列排空，再调用 `Start`。

#### `MonoBehaviourManager.TogglePause`

**签名：**
`public static void TogglePause(string channel = DEFAULT_CHANNEL)`

**返回：** `void`

**说明：**
- 运行中则暂停，暂停中则恢复；委托给 `Pause` / `Resume`。

### 注册

#### `MonoBehaviourManager.RegisterBehaviour`

**签名：**
`public static void RegisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `behavior` | `IMonoBehaviour` | 要添加的行为实例。 |
| `channel` | `string` | 目标通道。 |

**返回：** `void`

**说明：**
- 入队后在下一帧开始处理；管理器在注册时依次调用 `InvokeAwake()` 与 `InvokeStart()`。

#### `MonoBehaviourManager.UnregisterBehaviour`

**签名：**
`public static void UnregisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `behavior` | `IMonoBehaviour` | 要移除的行为实例。 |
| `channel` | `string` | 其所在通道。 |

**返回：** `void`

**说明：**
- 入队后在下一帧开始处理；包装对象归还给对象池。

### 配置

#### `MonoBehaviourManager.SetTargetFPS`

**签名：**
`public static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `fps` | `int` | 目标每秒帧数，钳位 `1..1000`。 |

**返回：** `void`

**示例：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 50 行）
MonoBehaviourManager.SetTargetFPS(30, "game");
```

**说明：**
- 经配置队列在下一帧边界生效。

#### `MonoBehaviourManager.SetFixedUpdateInterval`

**签名：**
`public static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `intervalMs` | `int` | 两次固定更新之间的毫秒数，合法 `1..1000`，越界被忽略。默认 `16`。 |

**返回：** `void`

**备注：**
- 交给 FixedUpdate 泵并在它那条线程上应用 —— 也就是被修改的那个步长的属主线程。

#### `MonoBehaviourManager.SetTimeScale`

**签名：**
`public static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `timeScale` | `float` | 该通道时间源的播放速率。默认 `1.0`。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentOutOfRangeException` | 值为负。时间源不倒着走。 |

**备注：**
- 立即作用于该通道的时间源，不经过配置队列：时间源自己串行化写入。
- 它缩放的是**整条虚拟时钟**，所以 `FrameEventArgs.DeltaTime` 与 `FrameEventArgs.TotalTime` 都随它变化；经由 `MonoBehaviourManager.Bus` 锚到同一时间源上的动画也一样。
- 速率为 `0` 会冻结时钟但不算暂停：不再派发帧，而且 `Resume` 不会让它重新走起来 —— 只有非零速率可以。

**示例：**
```text
// 时间缩放 0.5 让每个 FrameEventArgs.DeltaTime 减半，TotalTime 也以半速累计
MonoBehaviourManager.SetTimeScale(0.5f, "game");
```

#### `MonoBehaviourManager.ExecuteOnMainThread`

**签名：**
`public static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `action` | `Action` | 在下一帧开始时执行的委托。 |

**返回：** `void`

**说明：**
- 更新线程每帧最多排空 64 个动作（见 `ProcessMainThreadOperations`）。在 UI 宿主中仍需自行封送到调度器（Dispatcher）。

#### `MonoBehaviourManager.SetUseAsyncLoop`

**签名：**
`public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `useAsyncLoop` | `bool` | `true` 时以 `async`/`await` + `Task.Delay` 替代原生线程驱动循环。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | 通道已在运行。 |

**说明：**
- 仅为该通道覆盖全局 `UseAsyncLoop`（由 `MonoBehaviourManagerTests.SetUseAsyncLoop_*` 验证）。

#### `MonoBehaviourManager.ClearUseAsyncLoopOverride`

**签名：**
`public static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)`

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | 通道已在运行。 |

**说明：**
- 移除该通道的独立覆盖，回退到全局 `UseAsyncLoop`。

### 状态查询

所有状态查询共享 `(string channel = DEFAULT_CHANNEL)` 形态；当通道从未创建时返回 `false` / `0` / `"Stopped"`。

| 成员 | 返回 |
|---|---|
| `IsRunning` | `bool` |
| `IsPaused` | `bool` |
| `CurrentFPS` | `int` |
| `TargetFPS` | `int` |
| `TotalTime` | `TimeSpan` |
| `TotalTimeMs` | `long` |
| `TotalFrames` | `long` |
| `ActiveBehaviorCount` | `int` |
| `TimeScale` | `float` |
| `SystemStatus` | `string` — `"Stopped"` / `"Paused"` / `"Running"` |
| `IsUpdateThreadAlive` | `bool`（带 2 秒无活动超时） |
| `IsFixedUpdateThreadAlive` | `bool`（带 2 秒无活动超时） |

两个存活查询在该通道的时钟停摆期间也返回 `true`：park 住的泵是在等一个信号，而不是闲下来，所以无活动超时对它不适用。

#### `MonoBehaviourManager.Bus`

**签名：**
`public static ITimeSourceControl? Bus(string channel = DEFAULT_CHANNEL)`

**返回：** 该通道的时间源；通道从未创建过时返回 `null`。

**备注：**
- 通道的帧与锚到这个源上的所有东西共享同一条时钟：把它交给 `Transition.Execute(target, bus)` 之后，`Pause`、`Resume` 与 `SetTimeScale` 会同时作用于动画与帧。
- 该源在通道构造时经 `TimerCore.CreateTimeSource<ITimeSourceControl>()` 解析，所以平台可以在那里注册自己的实现来替换。默认实现是 `TimeSourceCore`，位于 `VeloxDev.Timing` 命名空间。

**示例（状态查询）：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 158、182-188 行）
MonoBehaviourManager.TotalFrames();
MonoBehaviourManager.ActiveBehaviorCount();
MonoBehaviourManager.IsUpdateThreadAlive();
MonoBehaviourManager.IsFixedUpdateThreadAlive();
MonoBehaviourManager.IsRunning();
MonoBehaviourManager.IsPaused();
```

### 事件

#### `MonoBehaviourManager.OnChannelStarted`

**签名：**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStarted`

**说明：**
- 通道循环启动时以通道名触发。

#### `MonoBehaviourManager.OnChannelPaused`

**签名：**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelPaused`

#### `MonoBehaviourManager.OnChannelResumed`

**签名：**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelResumed`

#### `MonoBehaviourManager.OnChannelStopped`

**签名：**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStopped`

**示例（订阅）：**
```text
MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine($"OnChannelStarted -> {e.ChannelName}");
```

### 属性

#### `MonoBehaviourManager.UseAsyncLoop`

**签名：**
`public static bool UseAsyncLoop { get; set; }`

**说明：**
- 默认值取自所链接的 `VeloxDev.Core` 程序集的构建目标。在 .NET 5+ 目标上，仅当运行于浏览器（`OperatingSystem.IsBrowser()`，WASM）或 iOS（`OperatingSystem.IsIOS()`）时才初始化为 `true`；其余环境默认 `false`（原生线程）。在 .NET 5 之前的目标（`netstandard2.0`、`netcoreapp3.0`、`netframework4.6.1`）上，因 `OperatingSystem.IsBrowser` 不可用，初始化回退为 `true`。
- `SetUseAsyncLoop` / `ClearUseAsyncLoopOverride` 可按通道覆盖该全局值。

#### `MonoBehaviourManager.ChannelNames`

**签名：**
`public static IEnumerable<string> ChannelNames { get; }`

**返回：** `IEnumerable<string>` — 所有已创建通道的名称。
