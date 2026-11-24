# Prerequisites

## Supported targets

Source: `Src/Adapters/VeloxDev.WinUI/VeloxDev.WinUI.csproj`.

| Property | Declared value |
| --- | --- |
| `TargetFrameworks` | `net8.0-windows10.0.19041.0;net10.0-windows10.0.19041.0` |
| `TargetPlatformMinVersion` | `10.0.17763.0` |
| `UseWinUI` | `true` |
| `Microsoft.WindowsAppSDK` | `1.6.241114003` (adapter dependency) |
| `VeloxDev.Core` dependency | `12.3.0` |
| Package version | `12.3.0` |

The trimmed demo targets `net10.0-windows10.0.19041.0` and references `Microsoft.WindowsAppSDK` `1.8.251003001`; that is the **tested** configuration, not the minimum. This page uses `net8.0-windows10.0.19041.0`.

## Tooling

- **.NET SDK 8.0 or later** and the **Windows App SDK** build tooling (`UseWinUI`).
- **Windows 10 version 1809 (build 17763) or later** — the declared platform minimum.
- A **`win-x64` (or matching) runtime identifier**. The demo pins `win-x64`; add the other RIDs only if you publish for them.
- No database, service, API key or network access.

## Add the packages

```powershell
dotnet add package VeloxDev.WinUI --version 12.3.0
dotnet add package Microsoft.WindowsAppSDK --version 1.6.241114003
dotnet add package Microsoft.Windows.SDK.BuildTools --version 10.0.26100.6584
```

**Expected result:** the commands exit `0`; the project file lists all three and `VeloxDev.Core` is restored transitively.

The adapter package carries the Core generator as an analyzer dependency, so the `[WorkflowBuilder.*]` and `[VeloxProperty]` attributes generate `InitializeWorkflow()` and the standard commands.

## Project settings

```xml
<PropertyGroup>
  <OutputType>WinExe</OutputType>
  <TargetFramework>net8.0-windows10.0.19041.0</TargetFramework>
  <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
  <RootNamespace>MyApp</RootNamespace>
  <RuntimeIdentifier>win-x64</RuntimeIdentifier>
  <UseWinUI>true</UseWinUI>
  <WindowsPackageType>None</WindowsPackageType>
  <EnableMsixTooling>true</EnableMsixTooling>
  <Nullable>enable</Nullable>
  <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
</PropertyGroup>
```

`WindowsPackageType=None` produces an unpackaged application. The WinUI project template supplies the `app.manifest` that declares Windows 10 compatibility and `PerMonitorV2` DPI awareness; the complete file set includes a minimal copy.

**Expected result:** `dotnet build` succeeds before any workflow type is added, and the output contains a `MyApp.exe`.
