# Install and Add the Analyzer

The feature needs two packages: the runtime library and the source generator. The generator is an **analyzer**, so it must not be referenced at runtime.

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

```text
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

A package places its generator under `analyzers/dotnet/cs`, so `dotnet add package` is enough — no `OutputItemType` is needed for a package reference. To keep the analyzer out of your own package's dependencies, mark it private:

```xml
<ItemGroup>
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

When working inside this repository, reference the generator project the way the demo does (`Examples/Tickable/WPF/Demo/Demo.csproj` lines 15-23) — a `ProjectReference` does **not** flow an analyzer to the referencing project:

```xml
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

**Expected result:** `dotnet build` succeeds. If the analyzer is missing, the build still succeeds — the failure appears when you use the generated surface: `CS0103` ("The name 'InitializeTickable' does not exist") or `CS1061` on the hook entry points. A class that is `partial` but never becomes `ITickable` almost always means the generator is not attached.

## 4. Confirm the generator is attached

Add a probe class and build:

```csharp
using VeloxDev.TimeLine;

[Tickable]
public partial class Probe
{
}

public static class Program
{
    public static void Main()
        => Console.WriteLine(typeof(Probe).GetInterfaces().Length);
}
```

**Expected result:** the program prints `1` — `Probe` implements `VeloxDev.TimeLine.ITickable`. To look at the generated file, build with `-p:EmitCompilerGeneratedFiles=true`; it then lands at

```text
obj/Debug/<tfm>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Tickable/<ClassName>_<NamespaceSegment>_Tick.g.cs
```

For the class `BouncingBall` in namespace `TickVerify` that is `BouncingBall_TickVerify_Tick.g.cs`; a class in the global namespace gets the segment `Global`. Without `EmitCompilerGeneratedFiles` the file is not written to disk at all — its absence there is not evidence that the generator did not run.
