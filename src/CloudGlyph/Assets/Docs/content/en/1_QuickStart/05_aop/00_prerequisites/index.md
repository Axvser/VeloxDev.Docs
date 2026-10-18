# Prerequisites

## Supported target

The whole AOP runtime is compiled under `#if NET` (`Src/Core/VeloxDev.Core/AspectOriented/*.cs`, `Interfaces/AspectOriented/IAspectOriented.cs`). `VeloxDev.Core.csproj` multi-targets `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`, and only the **`net5.0` and `net8.0` assets** define `NET`.

| Consumer TFM | AOP available |
|---|---|
| `net5.0` and later (`net6.0`, `net7.0`, `net8.0`, `net9.0`, `net10.0`, `net*-windows`) | Yes — takes the `net5.0` or `net8.0` asset |
| `netcoreapp3.0` | No — `NET` is not defined for .NET Core 3.x |
| `netstandard2.0`, `netframework4.6.1` | No — the runtime types do not exist |

A `net9.0` or `net10.0` project resolves the package's `net8.0` asset, which is built with `IsAotCompatible=true`. The proxy itself is generated C#, so there is no runtime code generation to break under trimming or NativeAOT.

## Toolchain

- **.NET SDK 8.0 or later.** The generator assembly references `Microsoft.CodeAnalysis.CSharp` 4.8.0 (`VeloxDev.Core.Generator.csproj`), which is the Roslyn version shipped with the .NET 8 SDK and Visual Studio 2022 17.8. This guide was verified with SDK 10.0.401.
- **C# 12 or later.** The generators require `LangVersion` 12 (`latest`) and report `VELOX_LANGVERSION001` below it.
- **NuGet / `dotnet` CLI.**

## Required services

None. AOP is a pure `VeloxDev.Core` + generator feature: no platform adapter, no database, no configuration file.

## Expected result

```bash
dotnet --version
```

prints `8.0.x` or later, and `dotnet --list-sdks` shows the same SDK.
