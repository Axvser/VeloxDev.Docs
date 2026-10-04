# MVVM — Install and Add a Reference

The MVVM runtime lives in the `VeloxDev.Core` package (namespace `VeloxDev.MVVM`); the two source generators live in the analyzer-only package `VeloxDev.Core.Generator` (namespace `VeloxDev.Generators`, classes `VeloxDev.Generators.MVVM` and `VeloxDev.Generators.Command`). `VeloxDev.Core.csproj` declares the generator as a package dependency for everything except `Debug`, so releasing both together brings the generators with Core.

## 1. From NuGet (consuming a released package)

```bash
dotnet add package VeloxDev.Core
```

`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` references `VeloxDev.Core.Generator` version `10.0.0` as a `PackageReference` whenever `Configuration != Debug`. The generator package carries its DLL under `analyzers/dotnet/cs`, so it is restored as an analyzer of *your* project — no manual analyzer wiring.

**Expected result:** the restore output lists `VeloxDev.Core.Generator`; `dotnet build` succeeds and the generator runs on your annotated classes.

## 2. From this repository (project reference)

A project reference does **not** flow analyzers, so every project that uses `[VeloxProperty]` / `[VeloxCommand]` has to add the generator itself. The demos do it with a `Debug`-only analyzer reference and a package reference for other configurations, exactly as in `Examples/MVVM/WPF/Demo/Demo.csproj` (path depth differs per project):

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

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                      OutputItemType="Analyzer"
                      ReferenceOutputAssembly="false"
                      Condition="'$(Configuration)' == 'Debug'" />
    <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                      Condition="'$(Configuration)' != 'Debug'" />
  </ItemGroup>

</Project>
```

**Expected result:** as soon as an annotated `partial` class is present, `dotnet build` succeeds and produced files appear under `obj/Debug/net9.0/generated/` (one `*_MVVM.g.cs` per class that has `[VeloxProperty]` members and one `*_Commands.g.cs` per class that has `[VeloxCommand]` methods).

## 3. Add the using

Every MVVM type is in namespace `VeloxDev.MVVM`, so a single `using` covers the attributes and the runtime:

```csharp
using VeloxDev.MVVM;
```

**Expected result:** `VeloxPropertyAttribute`, `VeloxCommandAttribute`, `IVeloxCommand`, `IVeloxCommandCompletion`, `IVeloxCommandStatus`, `VeloxCommand`, `VeloxCommandExtensions`, `CommandEventArgs`, `CommandEventHandler`, `CommandEventType`, `CommandOutcome`, `CommandCompletion` and `ObservableCollectionTracker` all resolve from this one namespace — no other `using` is required for the feature.

## Run declaration

- ✅ Actually built on 2026-10-01 (the commands below were run from the repository root; the transcript is the tail of each build):

  ```text
  dotnet build Examples/MVVM/WPF/Demo/Demo.csproj -c Debug
  Demo -> E:\VisualStudio\Projects\VeloxDev\Examples\MVVM\WPF\Demo\bin\Debug\net9.0-windows\Demo.dll
  已成功生成。0 个警告 0 个错误

  dotnet build Examples/MVVM/Avalonia/Demo/Demo.csproj -c Debug
  Demo -> E:\VisualStudio\Projects\VeloxDev\Examples\MVVM\Avalonia\Demo\bin\Debug\net9.0\Demo.dll
  已成功生成。0 个警告 0 个错误
  ```

- The NuGet route in step 1 was not executed (it needs a feed); its version numbers come from `VeloxDev.Core.csproj`. The project-reference shape in step 2 is copied from the two `Demo.csproj` files and *was* compiled by the build above.
