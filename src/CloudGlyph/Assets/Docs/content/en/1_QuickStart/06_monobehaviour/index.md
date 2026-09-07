# MonoBehaviour — Quick Start

## MonoBehaviour

The **monobehaviour** feature brings a Unity-style behaviour loop to plain .NET. You mark a `partial` class with `[MonoBehaviour]` and the Roslyn source generator (in assembly `VeloxDev.Core.Generator`) writes the bridge into `.g.cs`: the class implements the runtime interface `VeloxDev.MonoBehaviour.IMonoBehaviour` and gains the lifecycle entry points `Awake`, `Start`, `Update`, `LateUpdate` and `FixedUpdate` as `partial void` hooks that you can fill in on your own half of the class. There is no base class to inherit, no virtual `OnFrame` method and no `[Update]` attribute — the hook methods themselves are the API.

At runtime a static facade, `VeloxDev.TimeLine.MonoBehaviourManager`, drives named **channels**. Each channel owns two frame pumps: the Update pump (per-frame `Update` / `LateUpdate`, paced by a target FPS, default 60) and the FixedUpdate pump (a fixed-timestep `FixedUpdate`, default every 16 ms). Both pumps run on background threads (or `async` tasks when the platform forbids `Thread`, e.g. WASM/iOS) and invoke the hooks of every behaviour registered on that channel in registration order. The manager also carries per-channel configuration (`SetTargetFPS`, `SetFixedUpdateInterval`, `SetTimeScale`, `SetUseAsyncLoop`, `ExecuteOnMainThread`), lifecycle control (`Start`, `StopAsync`, `Pause`, `Resume`, `TogglePause`, `RestartAsync`) and status queries (`SystemStatus`, `IsRunning`, `CurrentFPS`, `TotalFrames`, `ActiveBehaviorCount`, ...).

Key public types and where they live:

- `VeloxDev.TimeLine.MonoBehaviourAttribute` — the class attribute with `channel` / `fps` arguments.
- `VeloxDev.TimeLine.MonoBehaviourManager` — the static channel runtime.
- `VeloxDev.TimeLine.FrameEventArgs`, `VeloxDev.TimeLine.TimeLineEventArgs`, `VeloxDev.TimeLine.ThreadSafeFrameEventArgs`, `VeloxDev.TimeLine.TransitionEventArgs` — the event-payload types passed to hooks.
- `VeloxDev.MonoBehaviour.IMonoBehaviour` — the interface the generator implements for you.
- `VeloxDev.TimeLine.MonoBehaviourChannelEventArgs` — payload of the channel `OnChannel*` events.

Everything is plain .NET (`VeloxDev.Core` targets `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`). **No UI adapter, no service, no configuration file** is needed for the loop itself — the only requirement for the generator is that the class is `partial`. A GUI demo ships for WPF (`Examples/MonoBehaviour/WPF/Demo`), and the loop is exercised headless by the tests in `Src/Core/VeloxDev.Core.Test/TimeLine/`.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages (they build toward the single runnable program on the last page):

- [00 Prerequisites](00_prerequisites/) — supported targets, SDK/runtime, and the "console host, no services" note
- [01 Install & Add a Reference](01_install/) — add `VeloxDev.Core` from NuGet or project-reference it from this repo
- [02 Define a Behaviour](02_define-a-behaviour/) — the `[MonoBehaviour]` class, `channel` / `fps`, and the generated `partial void` lifecycle hooks
- [03 Configure & Run the Loop](03_configure-and-run-the-loop/) — channel configuration knobs, `Start` / `StopAsync`, status queries and the channel events
- [04 Pause, Resume & Restart](04_pause-resume-and-restart/) — `Pause` / `Resume` / `TogglePause` / `RestartAsync` and their observable states
- [05 Frame Events & Thread Safety](05_frame-events-and-thread-safety/) — the event-payload types, the `Handled` flag, and the threading model
- [06 Verify & Complete Code](06_verify-and-complete-code/) — the demos and tests that exercise the feature, the single runnable program, and the run declaration
