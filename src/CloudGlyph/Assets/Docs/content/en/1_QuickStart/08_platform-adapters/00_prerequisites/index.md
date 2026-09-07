# Platform Adapters — Prerequisites

The supported targets below come from each adapter's **declared** `.csproj` (`Src/Adapters/<Package>/<Package>.csproj`) and its framework dependencies — not from the demos. A demo only proves one configuration that was *run*; it never defines the minimum support.

## Target frameworks

| Adapter package | `TargetFramework(s)` in `.csproj` | Framework dependency |
|---|---|---|
| `VeloxDev.WPF` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0` | `<UseWPF>true</UseWPF>` |
| `VeloxDev.WinForms` | `netframework4.6.1`; `net5.0-windows`; `netcoreapp3.0` | `<UseWindowsForms>true</UseWindowsForms>` |
| `VeloxDev.Avalonia` | `netstandard2.0`; `net6.0` | Avalonia `11.1.0` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0`; `net10.0-windows10.0.19041.0` | Windows App SDK (`UseWinUI`), min `10.0.17763.0` |
| `VeloxDev.MAUI` | `net10.0`; `net10.0-windows10.0.19041.0` | .NET MAUI workload (`UseMaui`), `Microsoft.Maui.Controls` |
| `VeloxDev.Razor` | `net6.0` | `Microsoft.AspNetCore.App` (Razor SDK) |
| `VeloxDev.Jalium` | `net10.0` | `Jalium.UI.Controls` |

Notes:

- `VeloxDev.MAUI` uses a platform-neutral `net10.0` assembly plus a `net10.0-windows10.0.19041.0` Windows TFM (the `#if WINDOWS` types, e.g. the WinUI-backed link/overlay path, only exist in the Windows asset). The Windows `SupportedOSPlatformVersion` is `10.0.17763.0`.
- `VeloxDev.WinUI` additionally declares a default `RuntimeIdentifier` of `win-x64` (also `win-arm64` / `win-x86`) and references `Microsoft.WindowsAppSDK`.
- `VeloxDev.Jalium` is platform-neutral (`net10.0`) — the adapter only uses the cross-platform Jalium core, so it serves Windows, Linux and Android consumers alike.

## SDK / runtime

- A .NET SDK able to build the **GUI workload** you pick: Windows-desktop TFMs need a Windows SDK (`net5.0-windows` / `netcoreapp3.0` / `net9.0-windows` …), WinUI needs the Windows App SDK workload, MAUI needs the `maui` workload, and Razor needs the Razor SDK (`Microsoft.NET.Sdk.Razor`). Avalonia and Jalium build anywhere the target SDK exists.
- This Quick Start's WPF scaffold targets `net9.0-windows` — a *tested* configuration (the in-repo demos build `net9.0-windows` / `net10.0`), not a requirement.
- **Package manager:** NuGet + the `dotnet` CLI (`dotnet new install`, `dotnet add package`, `dotnet build`).

## Required services

None. To *see* a workflow you need an app host — a WPF / WinForms / WinUI / Avalonia window, a MAUI app, a Blazor circuit (Razor), or a Jalium window — that displays the generated views and provides an `IWorkflowTreeViewModel` as the `DataContext`.

## Evidence note

WPF, Avalonia, WinUI, WinForms, MAUI, Blazor/Razor and Jalium all have workflow demos under `Examples/Workflow/<Platform>` (each with a `Trimmed` sibling) plus Transition/Theme demos under `Examples/Transition/*` and `Examples/Theme/*`. Because a GUI cannot be launched in this authoring environment, everything below is statically verified (see the run declaration on the Complete Code page).
