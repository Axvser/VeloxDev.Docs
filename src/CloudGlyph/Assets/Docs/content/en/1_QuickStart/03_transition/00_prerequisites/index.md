# Transition — Prerequisites

## 1. Supported targets

**Engine core** (from `VeloxDev.Core.csproj` `<TargetFrameworks>`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`. The engine core — including `VeloxDev.Timing`, `VeloxDev.Threading` and `VeloxDev.Lifetime` — is consumable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.

**Per-framework adapter targets** (from each adapter's csproj) — add the adapter that matches your GUI framework when you animate UI-bound properties:

| Adapter | `<TargetFrameworks>` |
|---|---|
| `VeloxDev.WPF` / `VeloxDev.WinForms` | `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0` |
| `VeloxDev.Avalonia` | `netstandard2.0` / `net6.0` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0` |
| `VeloxDev.MAUI` | `net10.0` plus the platform TFMs the MAUI workload adds (on Windows: `net10.0-windows10.0.19041.0`) |
| `VeloxDev.Razor` | `net6.0` |
| `VeloxDev.Jalium` | `net10.0` |

**SDK / runtime:** a .NET SDK that can build the target you pick. The engine core needs no special workload; the WPF / WinForms / WinUI / MAUI / Razor targets need the corresponding GUI workload (`<UseWPF>true</UseWPF>`, the Windows App SDK, the MAUI workload, the Razor SDK). The in-repo demos build against `net9.0` / `net10.0` — *tested* configurations, not requirements.

**Package manager:** NuGet via the `dotnet` CLI or Visual Studio (`dotnet add package ...`).

**Required services:** none — there is no database, key or external service. To *see* UI animations you need a running app host (a WPF/Avalonia/WinUI/WinForms window, a MAUI app, or a Blazor circuit); pure-value interpolation and the whole `VeloxDev.Timing` layer run headless.

## 2. Evidence for the examples

The demos this Quick Start mirrors are under `Examples/Transition/`:

| Demo | Target framework | What it animates |
|---|---|---|
| `WPF/Demo` | `net9.0-windows` | five `Rectangle`s — nested `TranslateTransform.X`, a `TransformGroup`, `Fill`, and five overshoot targets |
| `Avalonia/Demo` | `net9.0` | the same scenario set as WPF |
| `WinUI/Demo` | `net8.0-windows10.0.19041.0` | `Rectangle`s — `RenderTransform`, `Projection`, gradient `Fill` |
| `WinForms/Demo` | `net9.0-windows` | `Panel`/`Control`s — `Location`, `Size`, `BackColor` |
| `MAUI/Demo` | `net10.0-windows10.0.19041.0` on Windows (plus `net10.0-android` / `-ios` / `-maccatalyst`) | a MAUI `Rectangle` — `TranslationX/Y`, `RotationX/Y`, `Scale`, `Fill` |
| `Blazor/Demo` | `net10.0` (server + WASM client) | a plain `BoxModel` view-model re-rendered via `INotifyPropertyChanged` |
| `Jalium/Demo` | `net10.0-windows` | a Jalium desktop `Rectangle` |

The engine-level contract is additionally pinned by `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` (26 files) and `Src/Core/VeloxDev.Core.Test/Timing/*` (6 files).

## 3. The `AUTO TEST` conformance harness

`Examples/Transition/AUTO TEST/` is the strongest evidence available for this feature: a conformance harness that starts each demo's **executable**, drives it over UI Automation (and, for Blazor, Playwright against the installed Edge), and checks what actually happened on screen. It is deliberately **not** in `VeloxDev.slnx`, so `dotnet test` at the repository root stays backend-only — run it **by path**.

```bash
# 1. Build the demos FIRST, in exactly this form (no extra -p:Platform)
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

# 2. Run the acceptance suite (a stale demo binary looks exactly like a code bug)
cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

Four environment variables matter:

| Variable | Purpose |
|---|---|
| `VELOXDEV_AT=1` | **Required.** Without it every UI test reports as *skipped* and the run exits 0 — the single most common way to get a confident wrong answer out of this project. |
| `VELOXDEV_AT_PLATFORMS` | Comma-separated subset, e.g. `WPF,Avalonia`. Unset means all seven. |
| `VELOXDEV_AT_PACE` / `VELOXDEV_AT_OBSERVE` | Milliseconds to pause after every click / before every case. `0` = a verdict; the defaults (800 / 1200) = a run a person can watch. |
| `VELOXDEV_BENCH_MS` | How long each demo plays a sampler through a real transition. |

Per platform, four cases run, each pinning one half of the contract: `ObservationSurface_IsReachableAndTicking` (launch path, automation tree, self-ticking readout), `LoadModes_MatchTheLibrarySemantics` (mutual vs. concurrent, UI thread vs. background — observed as `nomutual=`), `EverySamplerMatchesItsClosedForm` (sampler arithmetic against an independently written closed form, plus a real transition run), and `TimelineControl_SteersTheRunningAnimation` (pause / resume / rate / seek on a live animation). Blazor adds a fifth that reads the browser's own computed style.

**Verified on this machine, 2026-10-01:** all seven demos built with 0 errors; the full suite ran `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` — 32 passed, 0 failed, 1 skipped (the `[Ignore]`d reachability stress test). See [Verify & Complete Code](../08_verify-and-complete-code/index.md) for the raw output.
