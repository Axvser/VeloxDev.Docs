# MVVM — Prerequisites

The MVVM layer is pure compile-time plus .NET runtime code: source generators produce the notification plumbing, and the runtime types are plain classes and interfaces in a `netstandard2.0` assembly. The feature has no GUI of its own, so everything below is usable from a headless console host as well as from the WPF / Avalonia desktop demos.

## 1. Supported targets and tooling

- **Supported targets** (declared in `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`): `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`, with `LangVersion` set to `latest`. The package is therefore consumable from .NET Framework 4.6.1+, .NET Core 3.0+, .NET 5+ and any newer runtime.
- **Source generator** (`Src/Generators/VeloxDev.Core.Generator/VeloxDev.Core.Generator.csproj`): `TargetFramework` `netstandard2.0`, `IsRoslynComponent` true, `Microsoft.CodeAnalysis.CSharp` **4.3.1** (private assets). That means Visual Studio 2022 17.3+ or .NET SDK 6.0.4xx and later can run it. The generator package declares version `10.0.0`; `VeloxDev.Core` is `10.0.0`.
- **Compiler language level** — the two annotation forms do not need the same one:
  - The **field** form `[VeloxProperty] private int _count;` and the `[VeloxCommand]` method forms use only `partial` methods and `partial` classes — available since C# 9, so they compile on every listed target.
  - The **`partial` property** form `[VeloxProperty] public partial string Greeting { get; set; }` requires C# 13 (a .NET 9+ SDK, or `LangVersion` ≥ 13 / `latest`). This form is optional.
  - Collection expressions (`= []`) used by the demos need C# 12.
- **Package manager:** NuGet or the `dotnet` CLI.
- **Demo configuration (tested, not required):** `Examples/MVVM/WPF/Demo` targets `net9.0-windows` with `<UseWPF>true</UseWPF>`; `Examples/MVVM/Avalonia/Demo` targets `net9.0` with Avalonia `11.3.0`.

**Expected result:** `dotnet --version` prints an SDK of at least 6.0.4xx (9.0+ if you want the `partial`-property form or the collection-expression initializers), and a NuGet feed is reachable.

## 2. Services you must supply

None. There is no database, no message bus, no DI container, no native interop and no configuration file. The feature does not even require a UI thread — it is a plain library you call from anywhere.

**Expected result:** no external service is needed; a `partial` class plus the attributes is the whole input surface.

## 3. No platform adapter

Because a generated command property is typed as `IVeloxCommand : System.Windows.Input.ICommand`, a XAML `Command="{Binding ...}"` binds through the host framework's own command system. The WPF and Avalonia demos use the feature with **no adapter package** — unlike the Transition and Dynamic Theme features, which do need a per-platform adapter. MVVM never touches the platform-adapters feature unless you want one of its animated command or theme layers on top.

**Expected result:** the MVVM demo builds with only a project reference to `VeloxDev.Core` (plus the analyzer reference for the generators); no `VeloxDev.WPF` or `VeloxDev.Avalonia` reference appears in `Demo.csproj`.

## Run declaration

- ✅ Partially executed on 2026-10-01. Compilation was actually run for this feature:

  ```text
  dotnet build Examples/MVVM/WPF/Demo/Demo.csproj -c Debug
    VeloxDev.Core.Generator -> ...\netstandard2.0\VeloxDev.Core.Generator.dll
    VeloxDev.Core           -> ...\net5.0\VeloxDev.Core.dll
    Demo                    -> ...\net9.0-windows\Demo.dll
  已成功生成。0 个警告 0 个错误

  dotnet build Examples/MVVM/Avalonia/Demo/Demo.csproj -c Debug
    Demo -> ...\net9.0\Demo.dll
  已成功生成。0 个警告 0 个错误
  ```

- The target-framework and version statements above are read from `VeloxDev.Core.csproj`, `VeloxDev.Core.Generator.csproj` and the two `Demo.csproj` files, not inferred from a successful build. The GUI window itself was not launched; verification of the visible behaviour happens on the last Quick Start page.
