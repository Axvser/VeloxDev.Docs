# Transition — Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj` `<TargetFrameworks>`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`. The engine core is consumable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **Per-framework adapter targets** (from each adapter's csproj) — add the adapter that matches your GUI framework when you animate UI-bound properties:
    - `VeloxDev.WPF` / `VeloxDev.WinForms`: `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - `VeloxDev.Avalonia`: `netstandard2.0` / `net6.0`
    - `VeloxDev.WinUI`: `net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0`
    - `VeloxDev.MAUI`: `net10.0` (plus the platform TFMs the MAUI workload adds, e.g. `net10.0-windows10.0.19041.0`)
    - `VeloxDev.Razor` (Blazor): `net6.0`
- **SDK / runtime:** a .NET SDK that can build the target you pick — the engine core needs no special workload, while the WPF / WinForms / WinUI / MAUI / Razor targets need the corresponding GUI workload (e.g. `<UseWPF>true</UseWPF>`, the Windows App SDK, the MAUI workload, the Razor SDK). The in-repo demos build against `net9.0` / `net10.0` — *tested* configurations, not requirements.
- **Package manager:** NuGet via the `dotnet` CLI or Visual Studio (`dotnet add package ...`).
- **Required services:** none — there is no database, key or external service. To *see* UI animations you need a running app host (a WPF/Avalonia/WinUI/WinForms window, a MAUI app, or a Blazor circuit); pure-value interpolation runs headless.

**Evidence for the examples.** The demos that this Quick Start mirrors are under `Examples/Transition/`:

| Demo | Target framework | What it animates |
|---|---|---|
| `WPF/Demo` | `net9.0-windows` | three `Rectangle`s — nested `TranslateTransform.X`, transform collections, `Fill` |
| `Avalonia/Demo` | `net9.0` | three `Rectangle`s — same scenario set as WPF |
| `WinUI/Demo` | `net8.0-windows10.0.19041.0` | `Rectangle`s — `RenderTransform`, `Projection`, gradient `Fill` |
| `WinForms/Demo` | `netframework4.7.1` | three `Panel`/`Control`s — `Location`, `Size`, `BackColor` |
| `MAUI/Demo` | `net10.0-*` | a MAUI `Rectangle` — `TranslationX/Y`, `RotationX/Y`, `Scale`, `Fill` |
| `Blazor/Demo` | `net10.0` (server + WASM client) | a plain `BoxModel` view-model re-rendered via `INotifyPropertyChanged` |
| `Jalium/Demo` | `net10.0-windows` | a Jalium desktop `Rectangle` |

The engine-level contract is additionally pinned by `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` (`EasesTests`, `InterpolatorCoreTests`, `SamplerSetTests`, `SamplingLoopTests`, `TransitionEffectCoreTests`, ...).
