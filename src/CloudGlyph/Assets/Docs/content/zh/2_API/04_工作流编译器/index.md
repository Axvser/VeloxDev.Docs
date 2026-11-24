# 工作流编译器

`CompilerViewModel.CompileAsync` 把一个节点可达的图转换成 `CompiledGraph`：由链、分支与扇出组构成的有序列表。编译图描述所有可能执行路径并固定每个节点的编译顺序；它不运行任何东西。

- [编译入口](00_编译入口/index.md) — `CompilerViewModel`、`CompileRole` 与两个遍历方向。
- [编译产物模型](01_编译产物模型/index.md) — `CompiledGraph`、各段类型、`NodeCompileInfo` 与 `CompiledOutline`。
- [编译期契约](02_编译期契约/index.md) — `ICompileContext`、`ICompileTimeRouter`、`RouterCompileMode` 与 `ICompileTimeAware`。

```csharp
var graph = (await new CompilerViewModel().CompileAsync(start, CompileRole.Root))[0];
foreach (var entry in graph.Entries)
    Console.WriteLine(entry.GetType().Name);
```

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`（程序集 `VeloxDev.Core`）。任务式教程见[工作流编译器](../../1_快速开始/04_工作流编译器/index.md)。
