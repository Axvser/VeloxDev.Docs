# MVVM — Prerequisites

The MVVM layer is pure compile-time + .NET runtime code: source generators produce the notification plumbing, and the runtime types are plain classes/interfaces in a `netstandard2.0` assembly. It has no GUI of its own, so everything below is usable from a headless console host as well as from the WPF/Avalonia desktop demos.

## 1. Supported targets & tooling

- **Supported target** (from `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`): `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`, with `LangVersion` set to `latest`. The package is consumable from .NET Framework 4.6.1+, .NET Core 3.0+, .NET 5+ and any newer runtime.
- **Source generator** (assembly `VeloxDev.Core.Generator`) is itself a `netstandard2.0` Roslyn component. Its csproj references `Microsoft.CodeAnalysis.CSharp` 4.3.1 — compatible with Visual Studio 2022 17.3+ / .NET SDK 6.0.4xx and later.
- **Compiler language level:**
  - The **field** form `[VeloxProperty] private int _count;` and the `[VeloxCommand]` method forms use only `partial` methods and `partial` classes — available since C# 9 / .NET 5, so they compile on every listed target.
  - The **`partial` property** form `[VeloxProperty] public partial int Count { get; set; }` requires C# 13 (a .NET 9+ SDK, or `LangVersion` ≥ 13 / `latest`). This is used in real code (e.g. `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs`) and is optional.
- **Package manager:** NuGet / the `dotnet` CLI.
- **Demo configuration (tested, not required):** `Examples/MVVM/WPF/Demo` targets `net9.0-windows` (WPF) and `Examples/MVVM/Avalonia/Demo` targets `net9.0` (Avalonia).

**Expected result:** `dotnet --version` prints an SDK of at least 6.0.4xx (9.0+ if you want the `partial`-property form); a NuGet feed is reachable.

## 2. Services you must supply

None. There is no database, no message bus, no DI container, no native interop and no configuration file. The feature does not even require a UI thread — it is a plain library you call from anywhere.

**Expected result:** no external service is needed; a `partial` class plus the attributes is the whole input surface.

## 3. No platform adapter

Because a generated command property is typed as `IVeloxCommand : System.Windows.Input.ICommand`, a XAML `Command="{Binding ...}"` binds with the host framework's own command system. WPF and Avalonia demos use the feature with **no adapter package** — this differs from the Transition/Theme features, which do need a per-platform adapter (see the `08_platform-adapters` feature). MVVM never touches the platform-adapters feature unless you want one of its animated command/theme layers on top.

**Expected result:** the MVVM demo builds with only a project reference to `VeloxDev.Core` (see the next page); no `VeloxDev.WPF` / `VeloxDev.Avalonia` reference appears in `Demo.csproj`.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Target frameworks come from `VeloxDev.Core.csproj` and the generator csproj; the demo configuration comes from `Examples/MVVM/*/Demo/Demo.csproj`.
