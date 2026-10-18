# Install

## From NuGet

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="VeloxDev.Core" Version="10.0.0" />
  </ItemGroup>
</Project>
```

The release package declares `VeloxDev.Core.Generator` as a package dependency; that package ships its DLL under `analyzers/dotnet/cs`, so both generators (`VeloxDev.Generators.AopSurface`, `VeloxDev.Generators.AopProxy`) run on the consumer's compilation automatically.

Alternatively:

```bash
dotnet add package VeloxDev.Core --version 10.0.0
```

**Expected result:** the command exits `0`, the `PackageReference` appears in the `.csproj`, and restore completes.

## Inside this repository

A `ProjectReference` does **not** carry analyzers transitively. The shipped demos therefore add the generator separately, as an analyzer — the pattern in `Examples/AOP/WPF/Demo/Demo.csproj`:

```xml
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

Without the analyzer reference the `[AspectOriented]` attribute still compiles, but no `Aop()` extension and no proxy class are generated — the failure appears as a missing-member compile error at the call site, not as a warning.

**Expected result:** `dotnet build` succeeds, and after a build with `EmitCompilerGeneratedFiles=true` the analyzer output directory contains three files per target class: `<Interface>.g.cs`, `<Interface>Proxy.g.cs`, and `<Class>_<Ns>_AopExt.g.cs`.
