# MonoBehaviour — `FrameEventArgs`

```csharp
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
| `DeltaTime` | `TimeSpan` | 自上一帧以来的缩放后增量时间。 |
| `TotalTime` | `TimeSpan` | 自通道启动以来的总时间。 |
| `CurrentFPS` | `int` | 实测帧率。 |
| `TargetFPS` | `int` | 配置的目标帧率。 |

**示例：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 24 行）
_velocity += Gravity * e.DeltaTime.TotalSeconds;
```

**说明：**
- 实例被池化复用；`internal` setter 保证只有管理器内部可修改（默认值由 `TimeLineEventArgsTests.FrameEventArgs_DefaultValues` 验证）。
