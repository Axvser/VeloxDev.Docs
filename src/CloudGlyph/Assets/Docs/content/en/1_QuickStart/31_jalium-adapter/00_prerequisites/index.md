# Prerequisites and install

## Supported targets

The adapter has a single target, `net10.0`, and depends on `Jalium.UI.Controls` **26.10.8** — the lowest platform-neutral package. It uses only the cross-platform controls, media and interop surface, so it can serve Windows, Linux and Android hosts.

- .NET SDK 10.0.
- A Jalium desktop host for this quick start: `net10.0-windows` plus `Jalium.UI.Desktop` 26.10.9. That package supplies the app host, windowing and build props; it is a demo dependency, not a requirement of the adapter.
- No database, service or API key.

`26.10.8` is a hard floor: `26.10.7` lacks `Dispatcher.MainDispatcher`, and earlier packages lack `DispatcherPriority`. A consumer may use a newer version.

## Packages

| Package | Version declared in this repository | Role |
| --- | --- | --- |
| `VeloxDev.Jalium` | 12.3.0 | the adapter |
| `VeloxDev.Core` | 12.3.0 | model and canvas contracts, pulled transitively |
| `Jalium.UI.Controls` | 26.10.8 (floor) | platform-neutral controls, media, interop |
| `Jalium.UI.Desktop` | 26.10.9 | desktop app host used by the demo |
| `VeloxDev.Jalium.Templates` | 12.0.0 | the seven `dotnet new` item templates |

## Project file

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net10.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="VeloxDev.Jalium" Version="12.3.0" />
    <PackageReference Include="Jalium.UI.Desktop" Version="26.10.9" />
  </ItemGroup>
</Project>
```

A cross-platform host targets `net10.0` and references `Jalium.UI.Controls` instead of `Jalium.UI.Desktop`; the adapter itself does not change.

## Install

```powershell
dotnet new console -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.Jalium
dotnet add package Jalium.UI.Desktop
dotnet new install VeloxDev.Jalium.Templates
```

The desktop demo's `Program.cs` is a plain `AppBuilder` entry point; the console template's `Main` is replaced in [Surface and host](../01_surface-and-host/index.md).

**Expected result:** the packages restore, and

```powershell
dotnet new list jalium-v
```

lists `jalium-v-tree`, `jalium-v-node`, `jalium-v-slot`, `jalium-v-link`, `jalium-v-selector`, `jalium-v-decorator`, `jalium-v-minimap`.

## Generate before the first build

The tree markup type-references `NodeView`, `LinkView`, `TemplateSelector`, `GridDecorator` and `MinimapOverlay`; the node markup references `SlotView`. A partial suite fails with `CS0246`. Generate all seven as shown in [Surface and host](../01_surface-and-host/index.md).

If a duplicate registration makes `dotnet new install` exit non-zero, run `dotnet new uninstall VeloxDev.Jalium.Templates` first.
