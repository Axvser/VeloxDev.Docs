# Tickable — Quick Start

The **tickable** feature brings a Unity-style frame loop to plain .NET, without Unity and without a base class. Mark a `partial` class with `[Tickable]` and the Roslyn source generator (assembly `VeloxDev.Core.Generator`) writes the bridge into a `.g.cs` file: the class gains the `VeloxDev.TimeLine.ITickable` implementation and five lifecycle hooks — `Awake`, `Start`, `Update`, `LateUpdate`, `FixedUpdate` — declared as `partial void`, which you fill in on your own half of the class.

At runtime the static facade `VeloxDev.TimeLine.TickManager` drives named **channels**. A channel owns two pumps:

- the **update pump** — one `Update` call per frame, then one `LateUpdate` call for every registered behaviour, paced by a target FPS (default 60);
- the **fixed-update pump** — a fixed-timestep `FixedUpdate`, default every 16 ms, which keeps count of the steps it missed and repays them.

Both pumps run on background threads named `VeloxDev.Update[<channel>]` / `VeloxDev.FixedUpdate[<channel>]`, or on `async` tasks when the platform cannot start `Thread`s (browser/WASM, iOS), selected by `TickManager.UseAsyncLoop`. Both park on one shared time source — the channel's *bus* — so one `TickManager.Pause(name)` freezes the frame callbacks and any animation anchored to the same clock together.

## Sub-pages

| Page | What it covers |
|---|---|
| [Prerequisites](00_prerequisites/index.md) | Declared target frameworks, SDK, and the "no service, no adapter, no config" note |
| [Install](01_install/index.md) | Adding `VeloxDev.Core` plus the `VeloxDev.Core.Generator` analyzer |
| [Define a Behaviour](02_define-a-behaviour/index.md) | The `[Tickable]` class, the `channel` / `fps` arguments, and the five generated hooks |
| [Configure and Run the Loop](03_configure-and-run-the-loop/index.md) | `Start` / `StopAsync`, the channel knobs, status queries and channel events |
| [Pause, Resume and Restart](04_pause-resume-and-restart/index.md) | `Pause` / `Resume` / `TogglePause` / `RestartAsync` and the states they produce |
| [Frame Events and Thread Safety](05_frame-events-and-thread-safety/index.md) | `FrameEventArgs`, the `Handled` flag, and the threading model |
| [Verify and Complete Code](06_verify-and-complete-code/index.md) | The complete runnable program and the Run Declaration |

## The shape of it

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]          // channel "demo", 60 fps
public partial class BouncingBall
{
    partial void Awake() { }                      // once, on registration
    partial void Start() { }                      // once, right after Awake
    partial void Update(FrameEventArgs e) { }        // every frame
    partial void LateUpdate(FrameEventArgs e) { }    // every frame, after all Update
    partial void FixedUpdate(FrameEventArgs e) { }   // every 16 ms by default
}
```

Everything else — implementing `ITickable`, forwarding each hook, registering on the channel — is generated. What remains yours is `InitializeTickable()`, the `TickManager` calls, and the hook bodies you care about.

## Where the evidence comes from

- **Demo (primary):** `Examples/Tickable/WPF/Demo/` — `MainWindow.Hooks.cs` holds the `[Tickable]` class, `SimState.cs` the shared state, `MainWindow.xaml.cs` the window that polls it.
- **Tests (secondary):** `Src/Core/VeloxDev.Core.Test/TimeLine/` — `TickManagerTests.cs`, `TickableAttributeTests.cs`, `TickableBusTests.cs`, `TimeLineEventArgsTests.cs`.
- **Source:** `Src/Core/VeloxDev.Core/TimeLine/` and `Src/Core/VeloxDev.Core/Interfaces/Tickable/`.
