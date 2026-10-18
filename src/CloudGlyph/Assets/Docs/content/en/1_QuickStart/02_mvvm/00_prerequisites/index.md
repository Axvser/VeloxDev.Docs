# MVVM — Prerequisites

The MVVM layer is compile-time generation plus plain .NET runtime code. It has no GUI of its own, so the same view-model works in a headless console host and in the WPF / Avalonia demos.

## 1. Supported targets and tooling

- **Runtime targets** — declared in `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`: `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`, with `LangVersion` `latest`. The package is consumable from .NET Framework 4.6.1+, .NET Core 3.0+, .NET 5+ and newer runtimes.
- **Generator** — `Src/Generators/VeloxDev.Core.Generator/VeloxDev.Core.Generator.csproj` targets `netstandard2.0`, sets `IsRoslynComponent` true, and references `Microsoft.CodeAnalysis.CSharp` **4.8.0** (private assets). That is the compiler shipped with the .NET 8 SDK, so any SDK 8.0+ can run it. The generator package version is `10.0.0`, the same as `VeloxDev.Core`.
- **Compiler language level** — the two annotation forms differ:
  - The field form `[VeloxProperty] private int _count;` and all `[VeloxCommand]` forms need only `partial` classes/methods: C# 9.
  - The `partial`-property form `[VeloxProperty] public partial string Greeting { get; set; }` needs C# 13 (a .NET 9+ SDK, or `LangVersion` ≥ 13).
  - Collection expressions (`= []`) used in the demos need C# 12.
- **Package manager** — NuGet, or the `dotnet` CLI.
- **Demo configuration (tested, not required)** — `Examples/MVVM/WPF/Demo` targets `net9.0-windows` with `<UseWPF>true</UseWPF>`; `Examples/MVVM/Avalonia/Demo` targets `net9.0` with Avalonia `11.3.0`.

**Expected result:** `dotnet --version` prints 8.0.x or newer; `dotnet nuget list source` shows a reachable feed.

## 2. Services you must supply

None. There is no database, message bus, DI container, native interop or configuration file, and the feature does not require a UI thread.

**Expected result:** a `partial` class plus the attributes is the whole input surface.

## 3. No platform adapter

A generated command property is an `IVeloxCommand`, which extends `System.Windows.Input.ICommand`, so XAML `Command="{Binding ...}"` binds through the host framework itself. Both demos reference only `VeloxDev.Core` (plus the analyzer); no `VeloxDev.WPF` or `VeloxDev.Avalonia` package appears in their `.csproj`.

**Expected result:** `Demo.csproj` contains a project reference to `VeloxDev.Core` and the generator wiring from the next page, and nothing else MVVM-related.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `VeloxDev.Core.csproj`, `VeloxDev.Core.Generator.csproj` and the two `Demo.csproj` files. The framework and version statements come from those files; the GUI windows were not launched.
