# Prerequisites

The contract lives in `VeloxDev.Core`, so it has no GUI dependency of its own. A GUI is needed only when you want to attach one of the adapters and observe the surface, and the conformance kit uses WPF for its smallest runnable example.

## Supported targets

These come from the project files, not from a demo run. A demo proves one tested configuration; it never defines the minimum.

| Assembly | Declared `TargetFrameworks` | Source |
|---|---|---|
| `VeloxDev.Core` | `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0` | `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` |
| `VeloxDev.WPF` | `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows` | `Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj` |
| `VeloxDev.Avalonia` | `netstandard2.0;net6.0;net8.0` | `Src/Adapters/VeloxDev.Avalonia/VeloxDev.Avalonia.csproj` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0;net10.0-windows10.0.19041.0` | `Src/Adapters/VeloxDev.WinUI/VeloxDev.WinUI.csproj` |
| `VeloxDev.MAUI` | `net10.0;net10.0-windows10.0.19041.0` | `Src/Adapters/VeloxDev.MAUI/VeloxDev.MAUI.csproj` |

## Tooling

- **.NET SDK 8.0 or later.** The WPF headless suite targets `net8.0-windows`.
- **A Windows machine for the WPF suite.** The other headless suites also need their platform's desktop toolchain; WinUI and MAUI have demos but no headless suite (see [Conformance](../03_conformance/index.md)).
- **MSTest 4.0.2** and **coverlet.collector 6.0.4** — the versions the headless test projects declare.

## Packages and references

For an application that only needs the contract types:

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
```

**Expected result:** the command exits `0`, and `VeloxDev.Core` appears in the project file.

The conformance kit is **not a NuGet package**. `Src/Test/Headless/VeloxDev.AdapterTestKit/VeloxDev.AdapterTestKit.csproj` sets `<IsPackable>false</IsPackable>`, so a conformance test references it as a project:

```xml
<ItemGroup>
  <ProjectReference Include="..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  <ProjectReference Include="..\..\Src\Adapters\VeloxDev.WPF\VeloxDev.WPF.csproj" />
  <ProjectReference Include="..\..\Src\Test\Headless\VeloxDev.AdapterTestKit\VeloxDev.AdapterTestKit.csproj" />
</ItemGroup>
```

**Expected result:** all three references resolve when the test project restores.

## What you need before the next page

- A test or application project whose target framework the chosen adapter supports.
- `VeloxDev.Core` reachable — directly, or transitively through an adapter package.
- No services, database, key or network access.

**Expected result:** `dotnet build` on the empty project succeeds before any surface code is added.
