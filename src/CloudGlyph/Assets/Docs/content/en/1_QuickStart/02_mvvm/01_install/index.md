# MVVM — Install and Add a Reference

The runtime is in the `VeloxDev.Core` package (namespace `VeloxDev.MVVM`). The generators ship in the analyzer-only package `VeloxDev.Core.Generator` (`VeloxDev.Generators.MVVM` and `VeloxDev.Generators.Command`).

## 1. From NuGet

```bash
dotnet add package VeloxDev.Core
dotnet add package VeloxDev.Core.Generator
```

`VeloxDev.Core.csproj` already references `VeloxDev.Core.Generator` `10.0.0` when `Configuration != Debug`, and the generator package packs its DLL under `analyzers/dotnet/cs`, so a normal `dotnet build` runs it. Adding the generator package explicitly is useful when the consumer's configuration is `Debug`, or when another project in the solution needs the analyzer without the Core package.

**Expected result:** restore lists both packages; `dotnet build` exits 0.

## 2. From this repository (project reference)

A project reference does **not** flow analyzers. Add the generator project with `OutputItemType="Analyzer"`, matching `Examples/MVVM/WPF/Demo/Demo.csproj`:

```xml
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
```

**Expected result:** after adding an annotated `partial` class, the build produces `{Class}_{Namespace}_MVVM.g.cs` for `[VeloxProperty]` members and `{Class}_{Namespace}_Commands.g.cs` for `[VeloxCommand]` methods under `obj/<Configuration>/<TargetFramework>/generated/`.

## 3. Add the using

```csharp
using VeloxDev.MVVM;
```

**Expected result:** the attributes and every runtime type (`IVeloxCommand`, `IVeloxCommandCompletion`, `IVeloxCommandResult`, `IVeloxCommandStatus`, `IVeloxCommand<TParam, TResult>`, `VeloxCommand`, `VeloxCommandExtensions`, `CommandEventArgs`, `CommandEventType`, `CommandOutcome`, `CommandCompletion`, `ObservableCollectionTracker`) resolve from this one namespace.

## Run declaration

- ⚠️ Not actually run in this documentation pass — the project-reference shape is copied from the two `Demo.csproj` files; the NuGet route was not executed.
