# Tick Loop

Drive an object's five lifecycle hooks from a named clock channel. `[Tickable]` generates the `ITickable` boilerplate; `TickManager` owns the threads, the target frame rate, the fixed step and the time scale.

## 1. Prerequisites

- **Supported targets of `VeloxDev.Core`**: `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`. The sample uses `net8.0`.
- **`VeloxDev.Core`** and **`VeloxDev.Core.Generator`** (the analyzer). The generator emits the `partial` hook declarations and the `ITickable` implementation.
- .NET SDK 8.0 or later. No services or GUI are required.

## 2. Install / Add Dependency

```text
dotnet new console -n TickQuickStart
cd TickQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** both packages restore. After the first build `InitializeTickable`, `CloseTickable` and the five `Invoke*` methods are available; set `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` to write the `*_Tick.g.cs` file under `obj/`.

## 3. Basic Setup / Registration

The attribute names the channel and, optionally, the target frame rate. A class needs `partial` because the generator adds the `ITickable` members and the partial hook declarations.

```csharp
using VeloxDev.TimeLine;

[Tickable("quickstart", fps: 60)]
public partial class Ticker
{
    partial void Awake() => System.Console.WriteLine("Awake");
    partial void Start() => System.Console.WriteLine("Start");
    partial void Update(FrameEventArgs e) { }
    partial void LateUpdate(FrameEventArgs e) { }
    partial void FixedUpdate(FrameEventArgs e) { }
}
```

**Expected result:** `new Ticker()` already implements `ITickable`. `InitializeTickable()` sets the channel's target FPS when `fps` is at least 1 and registers the object.

## 4. Core Usage (Step by Step)

### 4.1 Register, start, stop

```csharp
var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

// later
await TickManager.StopAsync("quickstart");
ticker.CloseTickable();
```

Registration only enqueues the lifecycle; the channel drains it before the first frame body. `Start` is idempotent. `CloseTickable()` unregisters, and registering the same object again reruns `Awake`/`Start` on a fresh wrapper.

**Expected result:** `Awake` prints once, then `Start` prints once, before the first `Update`.

### 4.2 The five hooks and their clocks

- `Awake` and `Start` run once per registration, before the first frame.
- `Update` runs once per frame on the channel's update thread with a variable `DeltaTime`.
- `LateUpdate` runs after `Update` on that same thread, unless `Update` set `e.Handled`.
- `FixedUpdate` runs on the fixed-update thread with a fixed `DeltaTime`, once per owed step; a stall is repaid as several calls in one wake-up.

`FrameEventArgs` also carries `TotalTime`, `CurrentFPS` and `TargetFPS`. One instance is reused for every hook of a frame, so a hook must not retain it.

**Expected result:** `Update` precedes `LateUpdate` in every frame that has both; `FixedUpdate` is independent of the frame count.

### 4.3 Suppressing the rest of a frame

```csharp
partial void Update(FrameEventArgs e)
{
    if (++_frames == 3)
    {
        e.Handled = true;   // no further Update bodies and no LateUpdate this frame
    }
}
```

The engine reads `Handled` between hooks. It does not affect `FixedUpdate`, which creates its own event args per step.

**Expected result:** on frame 3, `LateUpdate` does not run; on frame 4 it resumes.

### 4.4 Channel controls

```csharp
TickManager.SetTargetFPS(30, "quickstart");
TickManager.SetFixedUpdateInterval(33, "quickstart");   // milliseconds per fixed step
TickManager.SetTimeScale(0.5f, "quickstart");
TickManager.Pause("quickstart");
TickManager.Resume("quickstart");
TickManager.TogglePause("quickstart");
await TickManager.RestartAsync("quickstart");
```

`SetTimeScale(0f, ...)` freezes the clock but is not a pause: `IsPaused` stays false and `SystemStatus` still reports running. Read `TickManager.Bus(channel)` (`IsAdvancing`, `IsPaused`, `Rate`, `Epoch`, `Position`) when the consumer's park state matters.

**Expected result:** changing the target FPS changes the measured `CurrentFPS`; a time scale of 0 stops advancing without changing `IsPaused`.

### 4.5 Channels and multiple behaviours

Each channel has its own two threads, target FPS, fixed step and time scale. Behaviours registered on one channel are invoked on that channel's thread, sequentially. `TickManager.ChannelNames`, `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` and `OnBehaviorError` expose the manager's state; `TickManager.UseAsyncLoop` selects the loop shape, and `SetUseAsyncLoop(..., channel)` overrides it per channel.

```csharp
TickManager.RegisterBehaviour(other, "physics");
TickManager.SetTimeScale(2f, "physics");
```

**Expected result:** two channels advance independently; a behaviour on `physics` never runs on `quickstart`'s thread.

## 5. Verification

Run the complete program. `Awake` and `Start` appear once; `Update` and `LateUpdate` lines repeat, but frame 3 has no `LateUpdate`; `FixedUpdate` lines appear at the fixed step. After roughly 400 ms the summary prints `running=True` and a positive frame count.

## 6. Complete Code

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

await Task.Delay(400);

Console.WriteLine($"running={TickManager.IsRunning("quickstart")} frames={TickManager.TotalFrames("quickstart")}");

await TickManager.StopAsync("quickstart");
ticker.CloseTickable();

[Tickable("quickstart", fps: 60)]
public partial class Ticker
{
    private int _frames;

    partial void Awake() => Console.WriteLine("Awake");
    partial void Start() => Console.WriteLine("Start");

    partial void Update(FrameEventArgs e)
    {
        _frames++;
        if (_frames <= 3)
        {
            Console.WriteLine($"Update #{_frames} dt={e.DeltaTime.TotalMilliseconds:F1} ms fps={e.CurrentFPS}");
        }

        if (_frames == 3)
        {
            e.Handled = true;
        }
    }

    partial void LateUpdate(FrameEventArgs e)
    {
        if (_frames <= 4)
        {
            Console.WriteLine($"LateUpdate after Update #{_frames}");
        }
    }

    partial void FixedUpdate(FrameEventArgs e)
    {
        if (_frames <= 3)
        {
            Console.WriteLine($"FixedUpdate dt={e.DeltaTime.TotalMilliseconds:F1} ms");
        }
    }
}
```

The hook order, `Handled` behaviour and channel controls mirror `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` and `MainWindow.xaml.cs`.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs`, `TickableAttribute.cs`, `FrameEventArgs.cs`, `TimeLineEventArgs.cs`, `Src/Core/VeloxDev.Core/Interfaces/Tickable/ITickable.cs`, `Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` and the WPF tick demo. No build was performed in this environment.
