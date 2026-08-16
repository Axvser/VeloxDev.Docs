# Platform Adapters — Prerequisites

- **Supported targets** (from each adapter's csproj):
    - WPF / WinForms (`VeloxDev.WPF.csproj`, `VeloxDev.WinForms.csproj`): `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - Avalonia (`VeloxDev.Avalonia.csproj`): `netstandard2.0` / `net6.0`
    - WinUI (`VeloxDev.WinUI.csproj`): `net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0`
    - MAUI (`VeloxDev.MAUI.csproj`): `net10.0` (mobile TFMs)
    - Razor (`VeloxDev.Razor.csproj`): `net6.0`
- **SDK / runtime:** a .NET SDK that can build the GUI workload you pick (WPF/WinForms need a Windows TFM; WinUI needs the Windows App SDK; MAUI needs the MAUI workload; Razor needs the Razor SDK). The in-repo demos target `net9.0` / `net10.0` — *tested* configurations, not requirements.
- **Package manager:** NuGet / `dotnet` CLI (`dotnet new install`, `dotnet add package`, `dotnet build`).
- **Required services:** the GUI workload for your framework installed in the SDK (e.g. `Microsoft.NET.Sdk` with `<UseWPF>true</UseWPF>`, the WinUI Windows App SDK, the MAUI workload, or the Razor SDK); a running app host is required to *see* the UI — a WPF/Avalonia/WinUI/WinForms window or a Blazor circuit.
