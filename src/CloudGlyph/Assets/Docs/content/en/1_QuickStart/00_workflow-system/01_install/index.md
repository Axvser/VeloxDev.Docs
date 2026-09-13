# Workflow System — Install & Create the Project

## 1. Create a console project

```bash
cd E:\VisualStudio\Projects\VeloxDev        # the VeloxDev solution root
dotnet new console -n WorkflowQuickStart -f net10.0
cd WorkflowQuickStart
```

**Expected result:** a `WorkflowQuickStart.csproj` (Exe, `net10.0`) and `Program.cs` exist inside the solution root.

## 2. Reference the core engine

The engine lives in `Src/Core/VeloxDev.Core`. Add it as a project reference — the build pulls in the `VeloxDev.Core.Generator` source generator (version `9.0.0`) that emits the component plumbing:

```bash
dotnet add reference ..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj
```

(or, if you consume the produced NuGet package: `dotnet add package VeloxDev.Core`).

Make sure the project file enables nullable and implicit usings so it matches the engine's C# style:

```xml
<PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
</PropertyGroup>
```

**Expected result:** `dotnet restore` completes without errors, and a component file can `using VeloxDev.WorkflowSystem;` and `using VeloxDev.Core.WorkflowSystem.CompilerEx;`.

**Whole-tree JSON serialization** (used on the [Serialize & rebuild](../06_serialization/index.md) page) lives in the `VeloxDev.Core.Extension` project. Reference it the same way when you get to that step:

```bash
dotnet add reference ..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj
```

(or `dotnet add package VeloxDev.Core.Extension`). **Expected result:** a component file can also `using VeloxDev.MVVM.Serialization;`.

## 3. Where each API lives

| Namespace | Contents used by this guide |
|---|---|
| `VeloxDev.WorkflowSystem` | `WorkflowBuilder.Tree/Slot/Link/Node`, `TreeHelper`, `NodeHelper<T>`, `SlotHelper`, `LinkHelper`, `Anchor`, `Size`, `SlotChannel`, `TaskContext`, context interfaces |
| `VeloxDev.Core.WorkflowSystem.CompilerEx` | `CompilerViewModel`, `CompileRole`, `CompiledGraph`, `ChainSegment`, `BranchSegment`, `ParallelSegment`, `RuntimeEngine`, `RuntimeContext`, `ICompileContext`, `IRuntimeContext`, `ICompileTimeRouter`, `RouterCompileMode`, `IGroupData`, `IRedirectable` |
| `VeloxDev.MVVM` | `[VeloxProperty]`, `[VeloxCommand]` |

**Expected result:** each row maps to a real namespace — `using VeloxDev.WorkflowSystem;`, `using VeloxDev.Core.WorkflowSystem.CompilerEx;`, and `using VeloxDev.MVVM;` all compile in a component file of the new project.
