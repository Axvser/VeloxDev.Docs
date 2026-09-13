# MonoBehaviour — Install & Add a Reference

The runtime types and the source generator live in two packages. `VeloxDev.Core` (version `9.0.0` today) declares the runtime in namespaces `VeloxDev.TimeLine` and `VeloxDev.MonoBehaviour`; its `VeloxDev.Core.csproj` references the analyzer package `VeloxDev.Core.Generator` at the same version, so adding Core brings the `[MonoBehaviour]` generator with it. There is nothing else to configure — no UI adapter and no service registration for the loop.

## 1. From NuGet (consuming a released package)

```bash
dotnet add package VeloxDev.Core
```

Because `VeloxDev.Core` (current version `9.0.0`) lists `VeloxDev.Core.Generator` `9.0.0` as a package dependency, the generator assembly is restored as an analyzer of *your* project automatically. The checked-in WPF demo adds only a project reference to `VeloxDev.Core` yet its `[MonoBehaviour]` classes still compile, which confirms no separate analyzer reference or manual wiring is needed.

**Expected result:** the restore output lists `VeloxDev.Core.Generator`; `dotnet build` succeeds, and a `[MonoBehaviour]` class (page [Define a Behaviour](../02_define-a-behaviour/)) compiles into an `IMonoBehaviour` implementation.

## 2. From this repository (project reference)

The checked-in demo uses a direct project reference to the Core source project instead of the package. This is the reference shape from `Examples/MonoBehaviour/WPF/Demo/Demo.csproj` (the relative path depth differs per project):

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net10.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <UseWPF>true</UseWPF>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

Building Core from source compiles the generator into the build and feeds it to the referencing project, so the `.g.cs` partial appears as soon as you annotate a class.

**Expected result:** after adding the reference, `dotnet build` succeeds; a class annotated in the next step causes the compiler to emit a generated partial named `{ClassName}_{NamespaceWithDotsAsUnderscores}_Mono.g.cs` (for example `FrameCounter_MonoQuickStart_Mono.g.cs`).

## 3. Add the using

The attribute and the manager live in `VeloxDev.TimeLine`. Your own file only needs that one namespace for the attribute, the manager and the `FrameEventArgs` parameter types. The generated code references the interface namespace `VeloxDev.MonoBehaviour` itself, so you never type it:

```csharp
using VeloxDev.TimeLine;
```

**Expected result:** `MonoBehaviourAttribute`, `MonoBehaviourManager`, `FrameEventArgs` and the channel event args all resolve from this single namespace — no other `using` is required for the feature.

## Run declaration

- ⚠️ Statically verified only — the package commands and the `.csproj` shape were not executed while writing this page. Version numbers come from `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`; the reference shape comes from `Examples/MonoBehaviour/WPF/Demo/Demo.csproj`. The end-to-end build and run are recorded on the [Verify & Complete Code](../06_verify-and-complete-code/) page.
