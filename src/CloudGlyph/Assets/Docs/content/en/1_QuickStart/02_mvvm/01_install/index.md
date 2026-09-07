# MVVM — Install & Add a Reference

The MVVM runtime and both source generators live in the same two packages: `VeloxDev.Core` (runtime types in namespace `VeloxDev.MVVM`) and its analyzer package `VeloxDev.Core.Generator` (generator classes `VeloxDev.Generators.MVVM` / `VeloxDev.Generators.Command`). `VeloxDev.Core.csproj` references the generator at the same version, so adding Core brings the generators with it.

## 1. From NuGet (consuming a released package)

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core` (currently `8.0.0`) declares `VeloxDev.Core.Generator` `8.0.0` as a package dependency (`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`), so the generator assembly is restored as an analyzer of *your* project — no manual analyzer wiring.

**Expected result:** the restore output lists `VeloxDev.Core.Generator`; `dotnet build` succeeds.

## 2. From this repository (project reference)

All checked-in demos use this route instead — a direct project reference to the Core source project:

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

This is exactly the reference shape in `Examples/MVVM/WPF/Demo/Demo.csproj` and `Examples/MVVM/Avalonia/Demo/Demo.csproj` (the path depth differs per project). Building Core from source compiles the generator into the build and feeds it to the referencing project, so the generated `.g.cs` files appear when you annotate members.

**Expected result:** after adding the reference, `dotnet build` succeeds, and a partial class annotated in step 1 of the next page produces generator output under `obj/<Configuration>/<TargetFramework>/generated/` (e.g. `CounterViewModel_QuickStart_Mvvm_MVVM.g.cs` and `CounterViewModel_QuickStart_Mvvm_Commands.g.cs`).

## 3. Add the using

Every MVVM type is in namespace `VeloxDev.MVVM`. Annotated classes need it in the file that carries the attributes:

```csharp
using VeloxDev.MVVM;
```

**Expected result:** `VeloxPropertyAttribute`, `VeloxCommandAttribute`, `IVeloxCommand`, `VeloxCommand`, `CommandEventArgs`, `CommandEventHandler`, `CommandEventType` and `ObservableCollectionTracker` all resolve from this single namespace — no other `using` is required for the feature.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Version numbers and the generator dependency come from `VeloxDev.Core.csproj`; the reference shape comes from the MVVM demos' `Demo.csproj` files.
