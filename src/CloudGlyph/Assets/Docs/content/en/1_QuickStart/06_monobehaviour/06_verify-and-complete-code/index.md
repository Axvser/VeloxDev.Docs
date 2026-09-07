# MonoBehaviour — Verify & Complete Code

## 1. Verify with the demo

The feature ships one GUI demo, `Examples/MonoBehaviour/WPF/Demo` (`net10.0-windows`). Its `MainWindow.xaml.cs` shows the realistic WPF shape of the feature: the `MainWindow` itself is `[MonoBehaviour]`, and it also contains three nested `[MonoBehaviour] private partial class` components (`PhysicsComponent`, `InputComponent`, `RenderComponent`), each constructing itself and calling `InitializeMonoBehaviour()`. The window starts the default channel (`MonoBehaviourManager.Start()`), subscribes its own `Update` / `FixedUpdate` hooks, and every frame marshals the live stats onto the WPF dispatcher with `Dispatcher.Invoke` because the hooks run on loop threads. Buttons on the window call `Start`, `Pause`, `Resume` and `await StopAsync`; pressing H while Left Ctrl is held pops a statistics `MessageBox`.

**Expected result:** the status texts tick while running, freeze while paused, and a component added with "Add Component" joins the loop on the next frame (registration is queued, exactly as described on the [Define a Behaviour](../02_define-a-behaviour/) page).

## 2. Verify with the automated tests

The headless tests live in `Src/Core/VeloxDev.Core.Test/TimeLine/`:

- `MonoBehaviourAttributeTests.cs` — the attribute is class-only, not `AllowMultiple`, not `Inherited`, and constructs with no arguments.
- `MonoBehaviourManagerTests.cs` — `[DoNotParallelize]` because the manager holds shared static channel state. It pins the `SetUseAsyncLoop` / `ClearUseAsyncLoopOverride` contract: the override can be set (or cleared) before a channel starts and after it stops, but throws `InvalidOperationException` if the channel is already running, and the rule is per channel.
- `TimeLineEventArgsTests.cs` — default values of `FrameEventArgs` (`DeltaTime`/`TotalTime` zero, `CurrentFPS`/`TargetFPS` zero, `Handled` false), the empty `TransitionEventArgs`, and `ThreadSafeFrameEventArgs.Handled` surviving 100 concurrent reader/writer tasks without an exception.

**Expected result:** `dotnet test` on `VeloxDev.Core.Test` runs the `TimeLine` tests green.

## 3. Complete code

A single self-contained console program. It registers one `[MonoBehaviour]` counter on the `"game"` channel, subscribes the channel events, starts the loop, proves pause stops the pumps, resumes, reports the live statistics, restarts, and finally stops. All `using` directives are explicit; the only external requirement is a reference to `VeloxDev.Core` (page [Install & Add a Reference](../01_install/)):

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

namespace MonoQuickStart
{
    // A behaviour registered on the "game" channel, asking for 60 FPS.
    // The generator synthesizes the IMonoBehaviour bridge and the partial hooks.
    [MonoBehaviour(channel: "game", fps: 60)]
    public partial class FrameCounter
    {
        public long UpdateCount;
        public long FixedUpdateCount;

        public FrameCounter() => InitializeMonoBehaviour();   // registers this instance on "game"

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
            MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine($"[OnChannelStarted] {e.ChannelName}");
            MonoBehaviourManager.OnChannelStopped += (s, e) => Console.WriteLine($"[OnChannelStopped] {e.ChannelName}");

            MonoBehaviourManager.SetFixedUpdateInterval(16, "game");   // fixed-update thread ticks every 16 ms

            var counter = new FrameCounter();     // registers on the "game" channel (queued until the loop starts)
            Console.WriteLine("SystemStatus (before Start): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (before Start): " + MonoBehaviourManager.ActiveBehaviorCount("game"));

            MonoBehaviourManager.Start("game");
            await Task.Delay(120);               // the add-queue is drained at the top of a frame

            Console.WriteLine("SystemStatus (running): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (running): " + MonoBehaviourManager.ActiveBehaviorCount("game"));

            // Pause: neither the Update nor the FixedUpdate pump advances.
            MonoBehaviourManager.Pause("game");
            Console.WriteLine("SystemStatus (paused): " + MonoBehaviourManager.SystemStatus("game"));
            long a = Volatile.Read(ref counter.UpdateCount);
            await Task.Delay(300);
            long b = Volatile.Read(ref counter.UpdateCount);
            Console.WriteLine($"Updates grew while paused: {b - a}");

            MonoBehaviourManager.Resume("game");
            Console.WriteLine("SystemStatus (resumed): " + MonoBehaviourManager.SystemStatus("game"));

            await Task.Delay(800);
            Console.WriteLine($"UpdateCount: {Volatile.Read(ref counter.UpdateCount)}");
            Console.WriteLine($"FixedUpdateCount: {Volatile.Read(ref counter.FixedUpdateCount)}");
            Console.WriteLine($"CurrentFPS: {MonoBehaviourManager.CurrentFPS("game")}");
            Console.WriteLine($"TotalFrames: {MonoBehaviourManager.TotalFrames("game")}");
            Console.WriteLine($"TotalTimeMs: {MonoBehaviourManager.TotalTimeMs("game")}");
            Console.WriteLine($"IsUpdateThreadAlive: {MonoBehaviourManager.IsUpdateThreadAlive("game")}");

            // Restart = stop + clear statistics/queues + start again on the same channel.
            await MonoBehaviourManager.RestartAsync("game");
            await Task.Delay(120);
            Console.WriteLine("SystemStatus (after restart): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (after restart): " + MonoBehaviourManager.ActiveBehaviorCount("game"));
            Console.WriteLine("TotalFrames (right after restart): " + MonoBehaviourManager.TotalFrames("game"));

            await MonoBehaviourManager.StopAsync("game");
            Console.WriteLine("SystemStatus (after stop): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("TotalFrames (after stop): " + MonoBehaviourManager.TotalFrames("game"));
            Console.WriteLine("IsUpdateThreadAlive (after stop): " + MonoBehaviourManager.IsUpdateThreadAlive("game"));
        }
    }
}
```

No `...` — every identifier is defined above or resolves from the explicit `using` directives. The transcript below is the recorded output of one `Release` run; the counter and timing values vary per machine, but the ordering and the state transitions are stable across runs:

```text
SystemStatus (before Start): Stopped
ActiveBehaviorCount (before Start): 0
[OnChannelStarted] game
[Awake] behaviour registered
[Start] loop is running
SystemStatus (running): Running
ActiveBehaviorCount (running): 1
SystemStatus (paused): Paused
Updates grew while paused: 0
SystemStatus (resumed): Running
UpdateCount: 31
FixedUpdateCount: 33
CurrentFPS: 24
TotalFrames: 30
TotalTimeMs: 1240
IsUpdateThreadAlive: True
[OnChannelStopped] game
[OnChannelStarted] game
SystemStatus (after restart): Running
ActiveBehaviorCount (after restart): 1
TotalFrames (right after restart): 4
[OnChannelStopped] game
SystemStatus (after stop): Stopped
TotalFrames (after stop): 0
IsUpdateThreadAlive (after stop): False
```

Reading the transcript against the pages:

- `ActiveBehaviorCount (before Start): 0` then `[Awake]` / `[Start]` then `ActiveBehaviorCount (running): 1` — registration is queued and only picked up once the loop's first frame drains the add-queue (pages [Define a Behaviour](../02_define-a-behaviour/) and [Configure & Run the Loop](../03_configure-and-run-the-loop/)).
- `Updates grew while paused: 0` — `Pause` halts both pumps (page [Pause, Resume & Restart](../04_pause-resume-and-restart/)).
- After `RestartAsync`, statistics restart near zero (`TotalFrames (right after restart): 4`) while the behaviour stays registered and does not re-`Awake` (same page).
- After `StopAsync`, `TotalFrames (after stop): 0` shows the statistics reset, and `SystemStatus` returns to `"Stopped"`.

## 4. Run declaration

- ✅ Actually built and ran on 2026-09-07 (`dotnet run -c Release`, target `net10.0`, against a project reference to `VeloxDev.Core` from this repository). Recorded output is shown verbatim in section 3. Two earlier identical runs produced the same ordering and state transitions, with only the timing-dependent values (`FixedUpdateCount`, `TotalTimeMs`, `CurrentFPS`) differing.
