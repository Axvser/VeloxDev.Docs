# Tickable — Quick Start

The **tickable** feature brings a Unity-style frame loop to plain .NET, without Unity and without a base class. You mark a `partial` class with `[Tickable]` and the Roslyn source generator (assembly `VeloxDev.Core.Generator`) writes the bridge into a `.g.cs` file: the class gains the `VeloxDev.TimeLine.ITickable` implementation and five lifecycle hooks — `Awake`, `Start`, `Update`, `LateUpdate`, `FixedUpdate` — declared as `partial void`, which you fill in on your own half of the class. There is no `OnFrame` virtual to override, no `[Update]` method attribute, and nothing to inherit: the hook methods themselves are the API.

At runtime a static facade, `VeloxDev.TimeLine.TickManager`, drives named **channels**. A channel owns two pumps:

- the **Update pump** — one `Update` call per frame followed by one `LateUpdate` call for every registered behaviour, paced by a target FPS (default 60);
- the **FixedUpdate pump** — a fixed-timestep `FixedUpdate`, default every 16 ms, which owes each step it missed and repays them on its own thread.

Both pumps run on background threads named `VeloxDev.Update[<channel>]` / `VeloxDev.FixedUpdate[<channel>]`, or on `async` tasks when the platform forbids `Thread` (browser/WASM, iOS NativeAOT), selected by `TickManager.UseAsyncLoop`. Both park on a shared time source — the channel's *bus* — so one `TickManager.Pause(name)` freezes the frame callbacks and any animation anchored to the same clock together.

Feature name history: this capability was called *monobehaviour* before 2026-10-01 and the wiki directories were `06_monobehaviour` / `06_MonoBehaviour`. The namespace `VeloxDev.TimeLine` never changed; the type and member names did. See the API Reference for the full name map. The **lifecycle hook names did not change** — `Awake` / `Start` / `Update` / `LateUpdate` / `FixedUpdate` stay exactly as they always were.

## Quick Start — Sub-pages

The guide builds toward a single runnable program on the last page. Read them in order.

| Page | What it covers |
|---|---|
| [00 Prerequisites](00_prerequisites/index.md) | Supported target frameworks, SDK/runtime, and the "no service, no adapter, no config" note |
| [01 Install](01_install/index.md) | Adding `VeloxDev.Core` plus the `VeloxDev.Core.Generator` analyzer |
| [02 Define a Behaviour](02_define-a-behaviour/index.md) | The `[Tickable]` class, the `channel` / `fps` arguments, and the five generated hooks |
| [03 Configure and Run the Loop](03_configure-and-run-the-loop/index.md) | `Start` / `StopAsync`, the channel knobs, status queries and the channel events |
| [04 Pause, Resume and Restart](04_pause-resume-and-restart/index.md) | `Pause` / `Resume` / `TogglePause` / `RestartAsync` and the states they produce |
| [05 Frame Events and Thread Safety](05_frame-events-and-thread-safety/index.md) | `FrameEventArgs`, the `Handled` flag, and the threading model |
| [06 Verify and Complete Code](06_verify-and-complete-code/index.md) | The complete runnable program, the verification steps, and the Run Declaration |

## The shape of it

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]          // channel "demo", 60 fps
public partial class BouncingBall
{
    partial void Awake() { }            // once, on registration
    partial void Start() { }            // once, right after Awake
    partial void Update(FrameEventArgs e) { }        // every frame
    partial void LateUpdate(FrameEventArgs e) { }    // every frame, after all Update
    partial void FixedUpdate(FrameEventArgs e) { }   // every 16 ms by default
}
```

Everything else — implementing `ITickable`, forwarding each hook, registering on the channel — is generated. The rest of this guide is about the three lines that *are* yours: `InitializeTickable()`, some calls to `TickManager`, and the bodies of the hooks you care about.

## Where the evidence comes from

- **Demo (primary):** `Examples/Tickable/WPF/Demo/` — `MainWindow.Hooks.cs` holds the `[Tickable]` class, `SimState.cs` the shared state, `MainWindow.xaml.cs` the window that polls it.
- **Tests (secondary):** `Src/Core/VeloxDev.Core.Test/TimeLine/` — `TickManagerTests.cs`, `TickableAttributeTests.cs`, `TickableBusTests.cs`, `TimeLineEventArgsTests.cs`.
- **Source:** `Src/Core/VeloxDev.Core/TimeLine/` and `Src/Core/VeloxDev.Core/Interfaces/Tickable/`.
