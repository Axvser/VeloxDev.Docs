# MonoBehaviour — `FrameEventArgs`

命名空间 `VeloxDev.TimeLine`。逐帧事件参数，传给行为钩子 `Update(FrameEventArgs)`、`LateUpdate(FrameEventArgs)` 与 `FixedUpdate(FrameEventArgs)`。

```csharp
namespace VeloxDev.TimeLine;

public class FrameEventArgs : TimeLineEventArgs
{
    public TimeSpan DeltaTime { get; internal set; } = TimeSpan.Zero;
    public TimeSpan TotalTime { get; internal set; } = TimeSpan.Zero;
    public int CurrentFPS { get; internal set; } = 0;
    public int TargetFPS { get; internal set; } = 0;
}
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `DeltaTime` | `TimeSpan` | 距上一帧的增量时间，已按通道的时间缩放缩放。 |
| `TotalTime` | `TimeSpan` | 通道运行的总时长。 |
| `CurrentFPS` | `int` | 实测每秒帧数（每秒更新一次）。 |
| `TargetFPS` | `int` | 通道配置的目标帧率。 |
| `Handled`（继承） | `bool` | 自 `TimeLineEventArgs` 继承的 `virtual` 标志；`true` 会停止该帧阶段剩余行为。 |

**示例（WPF 示例中的真实用法）：**

```csharp
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 24 行）
_velocity += Gravity * e.DeltaTime.TotalSeconds;
```

**说明：**

- `internal` setter 让管理器每帧填充这些字段；使用者只读。实例被池化复用，请勿跨帧缓存 `FrameEventArgs`（默认值由 `TimeLineEventArgsTests.FrameEventArgs_DefaultValues` 验证）。

**源码：**

`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`
