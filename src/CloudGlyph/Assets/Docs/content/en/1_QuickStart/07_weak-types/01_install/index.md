# Weak Types — Install

All four weak types live in the `VeloxDev.Core` package (current version `10.0.0`), in the single namespace `VeloxDev.WeakTypes`. There is no separate adapter package, no source generator and no service registration for this feature — you add Core (or reference it) and the namespace is available.

## 1. From NuGet (consuming a released package)

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** the command exits `0` and a `<PackageReference Include="VeloxDev.Core" Version="10.0.0" />` appears in your `.csproj`. Because the four types multi-target `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0`, any project that can reference one of those receives them automatically.

## 2. From this repository (project reference)

To build against the source in this repo, add a project reference to the Core project. This is the exact shape the Quick Start console program on the final page uses (the relative path depth differs per project):

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

**Expected result:** `dotnet build` succeeds; a `net10.0` consumer resolves the `net8.0` build of `VeloxDev.Core` (the nearest compatible asset), not the `netstandard2.0` one.

## 3. Add the using

The four types share one namespace:

```csharp
using VeloxDev.WeakTypes;
```

**Expected result:** `WeakDelegate<>`, `WeakQueue<>`, `WeakStack<>` and `WeakCache<>` all resolve from this single `using` — no other namespace is required for the feature.

## Run declaration

- ⚠️ Not re-run during the 2026-10-18 revision — statically verified against `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` (TFMs and `Version`) and the package layout. The `net10.0` console shape in section 2 was previously compiled and executed; the end-to-end run transcript is on the [Verify & Complete Code](../08_verify-and-complete-code/) page.
