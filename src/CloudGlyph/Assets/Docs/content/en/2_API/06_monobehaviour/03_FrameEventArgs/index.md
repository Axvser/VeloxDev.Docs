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

| Member | Type | Description |
|---|---|---|
| `DeltaTime` | `TimeSpan` | Scaled delta time since the last frame. |
| `TotalTime` | `TimeSpan` | Total time since the channel started. |
| `CurrentFPS` | `int` | Measured frames per second. |
| `TargetFPS` | `int` | Configured target FPS. |

**Example:**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 24)
_velocity += Gravity * e.DeltaTime.TotalSeconds;
```

**Notes:**
- Instances are pooled and reused; `internal` setters keep mutation inside the manager (defaults verified by `TimeLineEventArgsTests.FrameEventArgs_DefaultValues`).
