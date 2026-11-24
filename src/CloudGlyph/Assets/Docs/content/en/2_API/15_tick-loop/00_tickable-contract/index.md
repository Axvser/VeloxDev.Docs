# Tickable Contract

The attribute, the interface the generator implements, and the event args a hook receives. Namespace `VeloxDev.TimeLine`; `ITickable` lives in `VeloxDev.TimeLine` via the interface file.

## VeloxDev.TimeLine

### Class: TickableAttribute

Names the channel and, optionally, the target frame rate.

**Signature:** `public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute`

| Member | Type | Default | Description |
|---|---|---|---|
| `Channel` | `string { get; }` | `"default"` | The channel this behaviour registers with. |
| `TargetFPS` | `int { get; set; }` | `-1` | Target FPS applied to the channel. `-1` leaves the channel's setting unchanged. |

**Attribute usage:** `AttributeTargets.Class`, `AllowMultiple = false`, `Inherited = false`.

The class must be `partial`: the generator adds the `ITickable` implementation and the five partial hook declarations.

### Interface: ITickable

**Signature:** `public interface ITickable`

| Member | Signature | Description |
|---|---|---|
| `InitializeTickable` | `void InitializeTickable()` | Registers this object with the channel. |
| `CloseTickable` | `void CloseTickable()` | Unregisters this object. |
| `InvokeAwake` | `void InvokeAwake()` | Runs the awake stage. |
| `InvokeStart` | `void InvokeStart()` | Runs the start stage. |
| `InvokeUpdate` | `void InvokeUpdate(FrameEventArgs e)` | Runs the update stage. |
| `InvokeLateUpdate` | `void InvokeLateUpdate(FrameEventArgs e)` | Runs the late-update stage. |
| `InvokeFixedUpdate` | `void InvokeFixedUpdate(FrameEventArgs e)` | Runs the fixed-update stage. |

### Class: TimeLineEventArgs

The base payload every timeline reports.

**Signature:** `public abstract class TimeLineEventArgs`

| Member | Type | Description |
|---|---|---|
| `Handled` | `virtual bool { get; set; }` | Set `true` to suppress the rest of the frame; default `false`. |
| `DeltaTime` | `TimeSpan { get; internal set; }` | Time since the previous frame; the fixed clock for `FixedUpdate`. |
| `TotalTime` | `TimeSpan { get; internal set; }` | Time since this line's clock started; excludes time spent stalled. |

### Class: FrameEventArgs

The payload a tick pump hands to a hook.

**Signature:** `public class FrameEventArgs : TimeLineEventArgs`

| Member | Type | Description |
|---|---|---|
| `CurrentFPS` | `int { get; internal set; }` | Frames the pump actually produced per second. |
| `TargetFPS` | `int { get; internal set; }` | Frames per second the channel was asked for. |

One instance is reused for every hook of a frame, so do not store it.

## Generated members

For `[Tickable("quickstart", fps: 60)] public partial class Ticker`, the generator emits (file `Ticker_{Namespace}_Tick.g.cs`):

| Member | Generated implementation |
|---|---|
| `InitializeTickable()` | Calls `TickManager.SetTargetFPS(60, "quickstart")` when `fps >= 1`, then `TickManager.RegisterBehaviour(this, "quickstart")`. |
| `CloseTickable()` | `TickManager.UnregisterBehaviour(this, "quickstart")`. |
| `InvokeAwake()` | Calls `Awake()`. |
| `InvokeStart()` | Calls `Start()`. |
| `InvokeUpdate(FrameEventArgs e)` | Calls `Update(e)`. |
| `InvokeLateUpdate(FrameEventArgs e)` | Calls `LateUpdate(e)`. |
| `InvokeFixedUpdate(FrameEventArgs e)` | Calls `FixedUpdate(e)`. |
| `partial void Awake()` | Implementation optional. |
| `partial void Start()` | Implementation optional. |
| `partial void Update(FrameEventArgs e)` | Implementation optional. |
| `partial void LateUpdate(FrameEventArgs e)` | Implementation optional. |
| `partial void FixedUpdate(FrameEventArgs e)` | Implementation optional. |

The class also declares `ITickable` in its base list.

## Example

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
        if (_frames == 3) e.Handled = true;   // no LateUpdate this frame
    }

    partial void LateUpdate(FrameEventArgs e) => Console.WriteLine("LateUpdate");
    partial void FixedUpdate(FrameEventArgs e) => Console.WriteLine($"fixed {e.DeltaTime.TotalMilliseconds:F1} ms");
}
```

Registration only enqueues the lifecycle; the channel runs `Awake` and `Start` before the first `Update`. See [Tick manager](../01_tick-manager/index.md) to start and stop the channel.
