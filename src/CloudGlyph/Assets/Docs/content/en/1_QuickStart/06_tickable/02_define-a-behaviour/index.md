# 02 · Define a Behaviour

A behaviour is one `partial` class carrying `[Tickable]`. The attribute selects the **channel** and, optionally, the channel's **target FPS**. Everything else about the class is ordinary C#.

## 1. The attribute

`Src/Core/VeloxDev.Core/TimeLine/TickableAttribute.cs`:

```csharp
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; } = channel;
    public int TargetFPS { get; set; } = fps;
}
```

Three things follow from that declaration, and all three are easy to get wrong:

- **A class only, no members.** `AllowMultiple = false` and `Inherited = false`, so a derived class does **not** inherit its base's `[Tickable]`. Every class that wants hooks carries the attribute itself.
- **The channel is a string.** It defaults to `TickManager.DEFAULT_CHANNEL`, which is the literal `"default"`.
- **`fps` is a target FPS, not a multiplier, and `-1` means "leave the channel alone".** When the value is `>= 1` the generated registration also calls `TickManager.SetTargetFPS(fps, channel)`; when it is `-1` no FPS call is emitted at all. `DemoChannel.Name` in the demo is `TickManager.DEFAULT_CHANNEL`, and the demo's class is declared `[Tickable(DemoChannel.Name)]` — channel only, `fps` left at `-1` so the window's own `SetTargetFPS(30, ...)` call is not overwritten. See `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` line 30.

## 2. The class

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]
public partial class BouncingBall
{
    partial void Awake() => Console.WriteLine("awake");
    partial void Start() => Console.WriteLine("start");
    partial void Update(FrameEventArgs e) { }
    partial void LateUpdate(FrameEventArgs e) { }
    partial void FixedUpdate(FrameEventArgs e) { }
}
```

**Expected result:** `dotnet build` succeeds. The generator has added a second declaration of `BouncingBall` implementing `ITickable`.

## 3. What the generator writes

The generator (`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs`) appends a partial class to the compilation. Stripped of the `global::` prefixes, `TickWriter.GenerateBody` (lines 69-122) emits:

```csharp
public void InitializeTickable()
{
    global::VeloxDev.TimeLine.TickManager.SetTargetFPS(60, "demo");
    global::VeloxDev.TimeLine.TickManager.RegisterBehaviour(this, "demo");
}

public void CloseTickable()
{
    global::VeloxDev.TimeLine.TickManager.UnregisterBehaviour(this, "demo");
}

public void InvokeAwake()        { Awake(); }
public void InvokeStart()        { Start(); }
public void InvokeUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)      { Update(e); }
public void InvokeLateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)  { LateUpdate(e); }
public void InvokeFixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e) { FixedUpdate(e); }

partial void Awake();
partial void Start();
partial void Update(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void LateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void FixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
```

Two consequences worth internalising:

- **The generated `SetTargetFPS` line only appears when `fps >= 1`.** With `[Tickable("demo")]` the line is absent and the channel keeps whatever FPS it already had.
- **`InitializeTickable()` and `CloseTickable()` are the only two things you ever call.** Nothing calls them for you. Registration is a *queue push*, so `InitializeTickable()` may be called before the channel starts — the drain happens on the channel's first frame.

## 4. The five hooks and when they run

| Hook | Runs on | Frequency |
|---|---|---|
| `Awake` | Update pump, first drain of the registration queue | Once per registration |
| `Start` | Update pump, immediately after `Awake` | Once per registration |
| `Update` | Update pump | Every frame |
| `LateUpdate` | Update pump | Every frame, after every behaviour's `Update` |
| `FixedUpdate` | FixedUpdate pump | Every step interval (default 16 ms), concurrently with the update pump |

`Awake` and `Start` run **before the first frame body**, on the update thread, from `ProcessAddedBehaviors` (`TickManager.cs` lines 785-801):

```csharp
var wrapper = _wrapperPool.Get();
wrapper.Reset(behavior, Interlocked.Increment(ref _instanceCounter));

_behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper;
SafeExecute(behavior.InvokeAwake);
SafeExecute(behavior.InvokeStart);
added = true;
```

Because that block is drained before the frame is sampled, a hook that reads `TickManager.TotalFrames(channel)` inside `Awake` observes the count **before** the first frame — which is what the WPF demo displays as its lifecycle evidence (`SimState.AwakeFrameOrdinal`).

**Expected result:** the class compiles, and you can point at five hook bodies you own and two generated methods you call.

## Notes

- Hooks are `partial void`, so an unimplemented one is simply removed by the compiler — there is no empty override to write and no cost for the ones you skip.
- `InvokeUpdate` and friends are the `ITickable` surface, not user API. Call the hooks' *entry points* (`InitializeTickable` / `CloseTickable`) and let the pump call the rest.
- Exceptions thrown out of a hook are caught per-behaviour and written to `Debug.WriteLine` (see `ExecuteBehaviorsUpdateSync`, `TickManager.cs` lines 689-702). A throwing hook never stops the loop and never surfaces on the console in a Release build.
