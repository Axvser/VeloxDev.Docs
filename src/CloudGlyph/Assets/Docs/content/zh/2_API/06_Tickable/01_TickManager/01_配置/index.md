# `TickManager` — 配置

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 1000-1103 行（静态表面）与第 201-270 行（`LoopChannel` 实现）。

这里的每个成员都接受 `string channel = TickManager.DEFAULT_CHANNEL`。

#### `TickManager.DEFAULT_CHANNEL`

**签名：**
`public const string DEFAULT_CHANNEL = "default";`

**返回：** `string` —— 所有省略 `channel` 参数的成员使用的通道名。

**说明：**
- 编译期常量，因此可用作参数默认值、特性实参和 `switch` 标签。
- `Examples/Tickable/WPF/Demo/SimState.cs` 第 21 行给出了值得照抄的写法：`public const string Name = TickManager.DEFAULT_CHANNEL;`，随后 `[Tickable(DemoChannel.Name)]` —— 通道只起一次名字，并在屏幕上被读回来。

#### 属性：`TickManager.UseAsyncLoop`

**签名：**
`public static bool UseAsyncLoop { get; set; }`

**返回：** `bool` —— 通道是否用 `async`/`await` + `Task.Delay` 而非原生 `Thread` 驱动帧。

**说明：**
- 初始化值取决于构建目标（第 1006-1011 行）：

```csharp
public static bool UseAsyncLoop { get; set; } =
#if NET5_0_OR_GREATER
    OperatingSystem.IsBrowser() || OperatingSystem.IsIOS();
#else
    true;
#endif
```

  也就是说，在 .NET 5+ 上只有运行于浏览器或 iOS 时才初始为 `true`，其余情况为 `false`（原生线程）；在 `netstandard2.0` / `netcoreapp3.0` / `netframework4.6.1` 这些目标上该 API 不可用，于是回退为 `true`。
- 在通道已存在之后改这个属性不会影响正在运行的通道 —— 该值是在 `Start` 时通过 `EffectiveUseAsyncLoop` 读取的。要按通道覆盖请用 `SetUseAsyncLoop`。

#### 属性：`TickManager.ChannelNames`

**签名：**
`public static IEnumerable<string> ChannelNames { get; }`

**返回：** `IEnumerable<string>` —— 静态 `_channels` 字典的键，即本进程中创建过的全部通道。

**说明：**
- 是 `ConcurrentDictionary.Keys` 的实时视图；在另一线程启动通道时枚举它是安全的，但是否包含该通道不确定。
- 创建过的通道永不移除。没有 `CloseChannel` —— 只有 `StopAsync`，它把通道及其时间源留在原处。

#### `TickManager.SetTargetFPS`

**签名：**
`public static void SetTargetFPS(int fps, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `fps` | `int` | 目标帧率。接受范围 `1..1000` |
| `channel` | `string` | 目标通道 |

**返回：** `void`。

**异常：** 无 —— 超范围的值被**静默忽略**，既不钳制也不上报（第 205-206 行）。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 75 行）
TickManager.SetTargetFPS(60, DemoChannel.Name);
```

**说明：**
- 以 `ConfigChangeRequest` 形式入队（从 `_configRequestPool` 取），由 update 泵在 `ProcessConfigChanges`（第 768-783 行）中施加，那里把目标帧率字段与缓存的帧时长一起写。
- 默认 60。该节奏约束的是*采样节拍*，不是虚拟时钟 —— 时间速率减半不会让帧率减半。

#### `TickManager.SetFixedUpdateInterval`

**签名：**
`public static void SetFixedUpdateInterval(int intervalMs, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `intervalMs` | `int` | 固定步之间的毫秒数。接受范围 `1..1000` |
| `channel` | `string` | 目标通道 |

**返回：** `void`。**异常：** 无 —— 超范围即忽略（第 223 行）。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 83 行）
TickManager.SetFixedUpdateInterval(16, DemoChannel.Name);
```

**说明：**
- 刻意**不**走配置队列：那条队列由 *update* 循环排空，而采样器属于 *fixed* 循环。该值写入一个 volatile 字段（`_pendingFixedIntervalMs`），由 fixed 泵在自己的线程上写进 `_fixedSampler.Step`（第 457-463 行）—— 从 update 线程写会与 `Advance` 争用它所重置的累加器。
- 默认 16 ms。步长为零不是合法值，所以零才可以被用来表示「没有待处理」。

#### `TickManager.SetTimeScale`

**签名：**
`public static void SetTimeScale(float timeScale, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `timeScale` | `float` | 通道时钟的速率，逐字施加到总线上。`1.0f` 为真实时间 |
| `channel` | `string` | 目标通道 |

**返回：** `void`。

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentOutOfRangeException` | `timeScale` 为负。总线拒绝倒走的时钟，而不是钳制它 |

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.xaml.cs（第 91 行）
TickManager.SetTimeScale(1f, DemoChannel.Name);

// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs（第 252 行）
Assert.ThrowsExactly<ArgumentOutOfRangeException>(() => TickManager.SetTimeScale(-1f, channel));
```

**说明：**
- 直接作用于总线（第 238 行）而不走配置队列：总线自己串行化它的写入者，而那条队列只在速率还是通道自有字段时才存在。
- 因为它是*时钟的*速率，`FrameEventArgs.DeltaTime` 与 `FrameEventArgs.TotalTime` 都随它变化，锚定在 `TickManager.Bus(channel)` 上的动画也一样 —— 而帧的*节拍*不变（`TickableBusTests.TheChannelsRateScalesTheAnimationButNotTheFrameCadence`）。
- 速率为 `0` 会冻结时钟但不构成暂停：不派发任何帧，`IsPaused` 保持 `false`，`SystemStatus` 仍报 `"Running"`，`Resume()` 也抬不动它。只有非零速率才行。

#### `TickManager.ExecuteOnMainThread`

**签名：**
`public static void ExecuteOnMainThread(Action action, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `action` | `Action` | 将在未来某一帧开头运行的委托 |
| `channel` | `string` | 目标通道 |

**返回：** `void`。

**说明：**
- 这里的「主线程」指的是通道的 **Update** 线程，不是 UI 线程。`ProcessMainThreadOperations`（第 753-766 行）每帧在排空配置/新增/移除队列之前最多取 64 个动作。
- 动作被 `try/catch` 包住，失败只写 `Debug.WriteLine`。
- 在 UI 宿主里你仍要自己封送到 dispatcher；而且在钩子里做这件事正是那种没有症状的失败 —— 引擎会吞掉钩子抛出的一切。

#### `TickManager.SetUseAsyncLoop`

**签名：**
`public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = TickManager.DEFAULT_CHANNEL)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `useAsyncLoop` | `bool` | `true` 表示本通道用 `async`/`await` + `Task.Delay` 驱动 |
| `channel` | `string` | 目标通道 |

**返回：** `void`。

**异常：**
| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | 通道已在运行。请先停止 |

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TickManagerTests.cs（第 36 行）
TickManager.SetUseAsyncLoop(true, TestChannel);   // Start 之前：成功

// 第 56 行
Assert.Throws<InvalidOperationException>(() => TickManager.SetUseAsyncLoop(true, ch));  // 运行中：抛
```

**说明：**
- 对全局属性 `UseAsyncLoop` 的按通道覆盖，存为可空布尔；运行时取值是 `_useAsyncLoopOverride ?? TickManager.UseAsyncLoop`。
- 该值在下次 `Start` 时生效，而不是调用时。异步路径与线程路径驱动同一条总线，因此暂停与速率在两者上表现一致（`TickableBusTests.TheAsyncLoopPathDrivesTheSameBus`）。

#### `TickManager.ClearUseAsyncLoopOverride`

**签名：**
`public static void ClearUseAsyncLoopOverride(string channel = TickManager.DEFAULT_CHANNEL)`

**返回：** `void`。

**异常：**
| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | 通道已在运行 |

**说明：**
- 丢弃按通道的覆盖，使该通道重新跟随全局 `UseAsyncLoop`。从未设置过覆盖时调用它不会抛（`TickManagerTests.ClearUseAsyncLoopOverride_WithoutSetting_DoesNotThrow`）。
