# 01 · Install & Add the Analyzer

The feature needs two packages: the runtime library and the source generator. The generator is an **analyzer**, so it must not be referenced at runtime — `ReferenceOutputAssembly="false"` in a project reference, or an `Analyzer` include from a package.

## 1. Create the project

```text
dotnet new console -n TickDemo
cd TickDemo
```

**Expected result:** a `TickDemo` directory with `TickDemo.csproj` and `Program.cs`; `dotnet run` prints `Hello, World!`.

## 2. Add the runtime library

```text
dotnet add package VeloxDev.Core --version 10.0.0
```

**Expected result:** `VeloxDev.Core` appears in the `<PackageReference>` list of `TickDemo.csproj`, and `dotnet build` restores it without errors.

## 3. Add the generator

From NuGet:

```text
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

Then make sure the package is treated as an analyzer rather than a library. In `TickDemo.csproj`:

```xml
<ItemGroup>
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

Or, when working inside this repository, reference the generator project the way the demo does — `Examples/Tickable/WPF/Demo/Demo.csproj` lines 15-23:

```xml
<!-- 本项目用 [Tickable]，analyzer 不随 ProjectReference 传递。 -->
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

**Expected result:** `dotnet build` succeeds. If the analyzer is missing you get no error at build time — you get `CS0103` / `CS0535` errors on the generated members the moment you try to use them. That failure mode is the one to watch for: a class that is `partial` but never becomes `ITickable` almost always means the generator is not attached.

## 4. Confirm the generator is attached

Add a throwaway class to `Program.cs` and build:

```csharp
using VeloxDev.TimeLine;

[Tickable]
public partial class Probe
{
}

// Program.cs
Console.WriteLine(typeof(Probe).GetInterfaces().Length);
```

**Expected result:** the project builds. To look at the generated file, build with `-p:EmitCompilerGeneratedFiles=true`; it then lands at

```text
obj/Debug/<tfm>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Tickable/<ClassName>_<NamespaceSegment>_Tick.g.cs
```

For the class `BouncingBall` in namespace `TickVerify` that is `BouncingBall_TickVerify_Tick.g.cs`; a class in the global namespace gets the segment `Global`. Without `EmitCompilerGeneratedFiles` the file is not written to disk at all — its absence there is not evidence that the generator did not run. If the generated members are missing from the compile, the analyzer is not attached — re-check step 3.
