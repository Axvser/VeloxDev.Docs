# MonoBehaviour — `MonoBehaviourManager`

常量：`public const string DEFAULT_CHANNEL = "default";`

#### 生命周期

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

#### 注册

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

#### 配置

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
| `intervalMs` | `int` | 两次固定更新之间的毫秒数，钳位 `1..1000`。默认 `16`。 |

**返回：** `void`

#### `MonoBehaviourManager.SetTimeScale`

**签名：**
`public static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `timeScale` | `float` | 作用于 `FrameEventArgs.DeltaTime` 的时间缩放，钳位 `0..10`。默认 `1.0`。 |

**返回：** `void`

**示例：**
```text
// 运行时探针，2026-08-17：SetTimeScale(0.5f) 使 DeltaTime 减半（比值 ≈ 0.49）
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

#### 状态查询

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

**示例（状态查询）：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 182-188 行）
MonoBehaviourManager.IsRunning();
MonoBehaviourManager.CurrentFPS();
MonoBehaviourManager.ActiveBehaviorCount();
MonoBehaviourManager.IsUpdateThreadAlive();
```

#### 事件

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
// 运行时探针，2026-08-17：打印 "event OnChannelStarted  -> demo"
MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine(e.ChannelName);
```

#### 属性

#### `MonoBehaviourManager.UseAsyncLoop`

**签名：**
`public static bool UseAsyncLoop { get; set; }`

**说明：**
- 在浏览器（WASM）与 iOS 上通过 `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()` 自动启用；其余平台默认 `false`（原生线程）。

#### `MonoBehaviourManager.ChannelNames`

**签名：**
`public static IEnumerable<string> ChannelNames { get; }`

**返回：** `IEnumerable<string>` — 所有已创建通道的名称。
