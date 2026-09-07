# MonoBehaviour — `FrameEventArgs`

Namespace `VeloxDev.TimeLine`. Per-frame event arguments delivered to the behaviour hooks `Update(FrameEventArgs)`, `LateUpdate(FrameEventArgs)` and `FixedUpdate(FrameEventArgs)`.

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

| Member | Type | Description |
|---|---|---|
| `DeltaTime` | `TimeSpan` | Delta time since the last frame, already scaled by the channel's time scale. |
| `TotalTime` | `TimeSpan` | Total running time of the channel. |
| `CurrentFPS` | `int` | Measured frames per second (updated once per second). |
| `TargetFPS` | `int` | Configured target FPS of the channel. |
| `Handled` (inherited) | `bool` | Virtual flag inherited from `TimeLineEventArgs`; `true` stops the remaining behaviours of the frame phase. |

**Example (real usage in the WPF demo):**

```csharp
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 24)
_velocity += Gravity * e.DeltaTime.TotalSeconds;
```

**Notes:**

- The `internal` setters let the manager fill the fields each frame; consumers only read them. Instances are pooled and reused, so do not cache a `FrameEventArgs` across frames (defaults verified by `TimeLineEventArgsTests.FrameEventArgs_DefaultValues`).

**Source:**

`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`
