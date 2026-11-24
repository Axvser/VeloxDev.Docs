# Workflow compiler

`CompilerViewModel.CompileAsync` turns the graph reachable from one node into a `CompiledGraph`: an ordered list of chains, branches and fan-out groups. The compiled graph describes every possible execution and fixes each node's compile order; it runs nothing.

- [Compiler entry](00_compiler-entry/index.md) — `CompilerViewModel`, `CompileRole` and the two walk directions.
- [Compiled model](01_compiled-model/index.md) — `CompiledGraph`, the segment types, `NodeCompileInfo` and `CompiledOutline`.
- [Compile-time contracts](02_compile-contracts/index.md) — `ICompileContext`, `ICompileTimeRouter`, `RouterCompileMode` and `ICompileTimeAware`.

```csharp
var graph = (await new CompilerViewModel().CompileAsync(start, CompileRole.Root))[0];
foreach (var entry in graph.Entries)
    Console.WriteLine(entry.GetType().Name);
```

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx` in `VeloxDev.Core`. For a task-oriented walkthrough, see [Workflow compiler](../../1_QuickStart/04_workflow-compiler/index.md).
