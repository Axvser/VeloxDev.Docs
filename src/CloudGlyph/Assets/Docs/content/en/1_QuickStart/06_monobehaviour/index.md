# MonoBehaviour — Quick Start

## MonoBehaviour

### Quick Start

#### 1. Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` — usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+) for the source generator; verified against SDK 9.0/10.0 — a *tested* environment, not a requirement. The WPF demo targets `net10.0-windows`.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:** none — the example uses a plain console host so the frame loop is observable from a terminal.


#### 2. Install / Add Dependency

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** The command exits `0`; a `<PackageReference Include="VeloxDev.Core" />` is added to the `.csproj` and restore completes. The package ships the runtime (`VeloxDev.TimeLine`, `VeloxDev.MonoBehaviour`) and depends on the source generator `VeloxDev.Core.Generator`, which turns `[MonoBehaviour]` classes into `IMonoBehaviour` implementations at compile time.

#### 3. Basic Setup / Registration

Declare a `[MonoBehaviour] partial` class and call `InitializeMonoBehaviour()` from the constructor. The generator emits `InitializeMonoBehaviour()` (which calls `MonoBehaviourManager.RegisterBehaviour(this, channel)`) and declares the partial hooks `Awake`, `Start`, `Update(FrameEventArgs)`, `LateUpdate(FrameEventArgs)`, `FixedUpdate(FrameEventArgs)`.

```csharp
using System.Threading;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public int UpdateCount;
    public int FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();   // registers this instance

    partial void Update(FrameEventArgs e)
    {
        Interlocked.Increment(ref UpdateCount);
    }
}
```

**Expected result:** The project compiles with no hand-written `IMonoBehaviour` implementation — the generator fills in the bridge. Instantiating `FrameCounter` registers it on the `"game"` channel.

#### 4. Core Usage (Step by Step)

**4.1 Configure the channel**

```csharp
MonoBehaviourManager.SetTargetFPS(60, "game");           // clamp: 1..1000
MonoBehaviourManager.SetFixedUpdateInterval(16, "game"); // ms, clamp: 1..1000
MonoBehaviourManager.SetTimeScale(1.0f, "game");         // clamp: 0..10
```

**Expected result:** The values are queued as config requests and applied at the start of the next frame; out-of-range values are silently clamped (source: `MonoBehaviourManager.cs` lines 184-210).

**4.2 Implement the lifecycle hooks**

```csharp
partial void Awake() => Console.WriteLine("[Awake] behaviour registered");

partial void Start() => Console.WriteLine("[Start] loop is running");

partial void Update(FrameEventArgs e)
{
    Interlocked.Increment(ref UpdateCount);
}

partial void LateUpdate(FrameEventArgs e)
{
}

partial void FixedUpdate(FrameEventArgs e)
{
    Interlocked.Increment(ref FixedUpdateCount);
}
```

**Expected result:** `Awake` and `Start` run once when the behaviour is picked up by the loop; `Update` and `LateUpdate` run every frame; `FixedUpdate` runs on the fixed-time thread every `SetFixedUpdateInterval` ms (default 16 ms).

**4.3 Start the loop**

```csharp
var counter = new FrameCounter();
MonoBehaviourManager.Start("game");
```

**Expected result:** `Start` spawns the Update and FixedUpdate threads (or async tasks when `UseAsyncLoop` is `true`) and fires `OnChannelStarted`. `SystemStatus("game")` returns `"Running"` and `ActiveBehaviorCount("game")` returns `1`.

**4.4 Stop the loop**

```csharp
await MonoBehaviourManager.StopAsync("game");
```

**Expected result:** Both threads are cancelled and joined (with a 1 s shutdown timeout), statistics are reset, queues are cleared, and `OnChannelStopped` fires. `SystemStatus("game")` returns `"Stopped"`.

#### 5. Verification

Run the complete program below and observe the frame counter. A sample run prints:

```text
[Awake] behaviour registered
[Start] loop is running
SystemStatus: Running
ActiveBehaviorCount: 1
CurrentFPS: 34
TotalFrames: 49
UpdateCount: 50
FixedUpdateCount: 54
SystemStatus after stop: Stopped
```

**Expected result:** `SystemStatus` reports `Running` while the loop is active; `UpdateCount` and `FixedUpdateCount` grow over the 1.5 s window; after `StopAsync` the status flips to `Stopped`.

#### 6. Complete Code

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public int UpdateCount;
    public int FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();

    partial void Awake() => Console.WriteLine("[Awake] behaviour registered");

    partial void Start() => Console.WriteLine("[Start] loop is running");

    partial void Update(FrameEventArgs e)
    {
        Interlocked.Increment(ref UpdateCount);
    }

    partial void LateUpdate(FrameEventArgs e)
    {
    }

    partial void FixedUpdate(FrameEventArgs e)
    {
        Interlocked.Increment(ref FixedUpdateCount);
    }
}

public static class Program
{
    public static async Task Main()
    {
        MonoBehaviourManager.SetTargetFPS(60, "game");
        MonoBehaviourManager.SetFixedUpdateInterval(16, "game");
        MonoBehaviourManager.SetTimeScale(1.0f, "game");

        var counter = new FrameCounter();
        MonoBehaviourManager.Start("game");

        await Task.Delay(1500);

        Console.WriteLine($"SystemStatus: {MonoBehaviourManager.SystemStatus("game")}");
        Console.WriteLine($"ActiveBehaviorCount: {MonoBehaviourManager.ActiveBehaviorCount("game")}");
        Console.WriteLine($"CurrentFPS: {MonoBehaviourManager.CurrentFPS("game")}");
        Console.WriteLine($"TotalFrames: {MonoBehaviourManager.TotalFrames("game")}");
        Console.WriteLine($"UpdateCount: {counter.UpdateCount}");
        Console.WriteLine($"FixedUpdateCount: {counter.FixedUpdateCount}");

        await MonoBehaviourManager.StopAsync("game");
        Console.WriteLine($"SystemStatus after stop: {MonoBehaviourManager.SystemStatus("game")}");
    }
}
```

#### 7. Run Declaration

- ✅ Actually built and ran on 2026-08-17. Recorded output (see §5): `[Awake] behaviour registered`, `[Start] loop is running`, `SystemStatus: Running`, `ActiveBehaviorCount: 1`, `CurrentFPS: 34`, `TotalFrames: 49`, `UpdateCount: 50`, `FixedUpdateCount: 54`, `SystemStatus after stop: Stopped`.
- The shipped WPF demo (`Examples/MonoBehaviour/WPF/Demo`) was not executed in this environment; the console example above exercises the same manager APIs (`Start`, `StopAsync`, `SetTargetFPS`, `SetFixedUpdateInterval`, `SetTimeScale`, status queries) and the generated lifecycle hooks.
