# Prerequisites

## Supported targets

Source: `Src/Adapters/VeloxDev.MAUI/VeloxDev.MAUI.csproj`.

| Property | Declared value |
| --- | --- |
| `TargetFrameworks` | `net10.0;net10.0-windows10.0.19041.0` |
| `UseMaui` | `true` |
| `MauiVersion` | `10.0.20` |
| `Microsoft.WindowsAppSDK` (Windows TFM) | `1.7.250909003` |
| Windows `SupportedOSPlatformVersion` | `10.0.17763.0` |
| `VeloxDev.Core` dependency | `12.3.0` |
| Package version | `12.3.0` |

The trimmed demo targets `net10.0-android`, plus `net10.0-ios`, `net10.0-maccatalyst` and `net10.0-windows10.0.19041.0` when the host OS allows. This page builds the Windows TFM only; the adapter also ships a platform-neutral `net10.0` asset.

The Windows TFM must be at least `net10.0-windows10.0.19041.0`: MAUI 10.0.x ships Windows assets only for that platform version (and 20348). A lower TFM silently falls back to the platform-neutral assembly and loses the Windows-only types the adapter's `#if WINDOWS` code needs.

## Tooling

- **.NET SDK 10.0 or later**, because the adapter targets `net10.0`.
- **The .NET MAUI workload** (`dotnet workload install maui`). The Windows target also needs the Windows App SDK runtime.
- **Windows 10 version 1809 (build 17763) or later** for the Windows TFM.
- No database, service, API key or network access.

## Add the packages

```powershell
dotnet add package VeloxDev.MAUI --version 12.3.0
dotnet add package Microsoft.Maui.Controls --version 10.0.20
```

On the Windows TFM, the project also needs Windows App SDK:

```xml
<ItemGroup Condition="$([MSBuild]::GetTargetPlatformIdentifier('$(TargetFramework)')) == 'windows'">
  <PackageReference Include="Microsoft.WindowsAppSDK" Version="1.7.250909003" />
</ItemGroup>
```

**Expected result:** the commands exit `0`; the project lists `VeloxDev.MAUI`, `Microsoft.Maui.Controls` and, for Windows, `Microsoft.WindowsAppSDK`; `VeloxDev.Core` is restored transitively.

## Project settings

```xml
<PropertyGroup>
  <TargetFramework>net10.0-windows10.0.19041.0</TargetFramework>
  <OutputType>Exe</OutputType>
  <RootNamespace>MyApp</RootNamespace>
  <UseMaui>true</UseMaui>
  <SingleProject>true</SingleProject>
  <ImplicitUsings>enable</ImplicitUsings>
  <Nullable>enable</Nullable>
  <MauiVersion>10.0.20</MauiVersion>
  <SupportedOSPlatformVersion>10.0.17763.0</SupportedOSPlatformVersion>
  <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
</PropertyGroup>
```

**Expected result:** `dotnet build` succeeds before workflow types are added and produces a Windows application.
