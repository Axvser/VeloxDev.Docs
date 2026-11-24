# 帧驱动契约

特性、生成器实现的接口，以及钩子收到的事件参数。命名空间 `VeloxDev.TimeLine`；`ITickable` 也在 `VeloxDev.TimeLine`。

## VeloxDev.TimeLine

### 类：TickableAttribute

命名通道，并可选地指定目标帧率。

**签名：** `public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute`

| 成员 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `Channel` | `string { get; }` | `"default"` | 此行为注册的通道。 |
| `TargetFPS` | `int { get; set; }` | `-1` | 应用到通道的目标 FPS。`-1` 保持通道原设置。 |

**特性用法：** `AttributeTargets.Class`，`AllowMultiple = false`，`Inherited = false`。

类必须是 `partial`：生成器添加 `ITickable` 实现与五个分部钩子声明。

### 接口：ITickable

**签名：** `public interface ITickable`

| 成员 | 签名 | 说明 |
|---|---|---|
| `InitializeTickable` | `void InitializeTickable()` | 向通道注册此对象。 |
| `CloseTickable` | `void CloseTickable()` | 取消注册。 |
| `InvokeAwake` | `void InvokeAwake()` | 运行 awake 阶段。 |
| `InvokeStart` | `void InvokeStart()` | 运行 start 阶段。 |
| `InvokeUpdate` | `void InvokeUpdate(FrameEventArgs e)` | 运行 update 阶段。 |
| `InvokeLateUpdate` | `void InvokeLateUpdate(FrameEventArgs e)` | 运行 late-update 阶段。 |
| `InvokeFixedUpdate` | `void InvokeFixedUpdate(FrameEventArgs e)` | 运行 fixed-update 阶段。 |

### 类：TimeLineEventArgs

每个时间轴报告的基础载荷。

**签名：** `public abstract class TimeLineEventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Handled` | `virtual bool { get; set; }` | 置 `true` 抑制本帧剩余部分；默认 `false`。 |
| `DeltaTime` | `TimeSpan { get; internal set; }` | 距上一帧的时间；对 `FixedUpdate` 是固定时钟。 |
| `TotalTime` | `TimeSpan { get; internal set; }` | 本时间轴时钟启动以来的时间；不含停摆时间。 |

### 类：FrameEventArgs

帧泵交给钩子的载荷。

**签名：** `public class FrameEventArgs : TimeLineEventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `CurrentFPS` | `int { get; internal set; }` | 帧泵实际每秒产出的帧数。 |
| `TargetFPS` | `int { get; internal set; }` | 通道被要求的每秒帧数。 |

同一帧的所有钩子复用同一实例，不要存储它。

## 生成的成员

对 `[Tickable("quickstart", fps: 60)] public partial class Ticker`，生成器产出（文件 `Ticker_{Namespace}_Tick.g.cs`）：

| 成员 | 生成的实现 |
|---|---|
| `InitializeTickable()` | `fps >= 1` 时调用 `TickManager.SetTargetFPS(60, "quickstart")`，然后 `TickManager.RegisterBehaviour(this, "quickstart")`。 |
| `CloseTickable()` | `TickManager.UnregisterBehaviour(this, "quickstart")`。 |
| `InvokeAwake()` | 调用 `Awake()`。 |
| `InvokeStart()` | 调用 `Start()`。 |
| `InvokeUpdate(FrameEventArgs e)` | 调用 `Update(e)`。 |
| `InvokeLateUpdate(FrameEventArgs e)` | 调用 `LateUpdate(e)`。 |
| `InvokeFixedUpdate(FrameEventArgs e)` | 调用 `FixedUpdate(e)`。 |
| `partial void Awake()` | 实现可选。 |
| `partial void Start()` | 实现可选。 |
| `partial void Update(FrameEventArgs e)` | 实现可选。 |
| `partial void LateUpdate(FrameEventArgs e)` | 实现可选。 |
| `partial void FixedUpdate(FrameEventArgs e)` | 实现可选。 |

该类还在基类列表中声明 `ITickable`。

## 示例

```csharp
using VeloxDev.TimeLine;

[Tickable("quickstart", fps: 60)]
public partial class Ticker
{
    private int _frames;

    partial void Awake() => Console.WriteLine("Awake");
    partial void Start() => Console.WriteLine("Start");

    partial void Update(FrameEventArgs e)
    {
        _frames++;
        if (_frames == 3) e.Handled = true;   // 本帧不运行 LateUpdate
    }

    partial void LateUpdate(FrameEventArgs e) => Console.WriteLine("LateUpdate");
    partial void FixedUpdate(FrameEventArgs e) => Console.WriteLine($"fixed {e.DeltaTime.TotalMilliseconds:F1} ms");
}
```

注册只是把生命周期入队；通道在首个 `Update` 之前运行 `Awake` 与 `Start`。启动与停止通道见[帧管理器](../01_帧管理器/index.md)。
