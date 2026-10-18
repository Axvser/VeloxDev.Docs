# 工作流系统 — 安装与创建项目

## 1. 创建控制台工程

```bash
cd E:\VisualStudio\Projects\VeloxDev        # VeloxDev 解决方案根目录
dotnet new console -n WorkflowQuickStart -f net10.0
cd WorkflowQuickStart
```

**预期结果：** 解决方案根目录下出现 `WorkflowQuickStart.csproj`（Exe，`net10.0`）与 `Program.cs`。

## 2. 引用核心引擎

引擎位于 `Src/Core/VeloxDev.Core`。用工程引用加入它 —— 构建会一并带入生成组件管线的 `VeloxDev.Core.Generator` 源生成器（版本 `10.0.0`）：

```bash
dotnet add reference ..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj
```

（若消费产出的 NuGet 包：`dotnet add package VeloxDev.Core`。）

确保工程文件启用可空与隐式 using，与引擎的 C# 风格一致：

```xml
<PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
</PropertyGroup>
```

**预期结果：** `dotnet restore` 无错误完成，组件文件可以 `using VeloxDev.WorkflowSystem;` 与 `using VeloxDev.Core.WorkflowSystem.CompilerEx;`。

**整棵树的 JSON 序列化**由 `VeloxDev.Core` 自身（`VeloxDev.Serialization`）提供 —— 「序列化与重建」页不需要额外包。`VeloxDev.Core.Extension` 只在用到 **Agent** 以及编译图 / 检查点文档时才需要：

```bash
dotnet add reference ..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj
```

（或 `dotnet add package VeloxDev.Core.Extension`。）**预期结果：** 组件文件还能 `using VeloxDev.Serialization;`。

## 3. 各 API 所在位置

| 命名空间 | 本指南用到的内容 |
|---|---|
| `VeloxDev.WorkflowSystem` | `WorkflowBuilder.Tree/Slot/Link/Node`、`TreeHelper`、`NodeHelper<T>`、`SlotHelper`、`LinkHelper`、`Anchor`、`Size`、`SlotChannel`、`TaskContext`、上下文接口 |
| `VeloxDev.Core.WorkflowSystem.CompilerEx` | `CompilerViewModel`、`CompileRole`、`CompiledGraph`、`ChainSegment`、`BranchSegment`、`ParallelSegment`、`RuntimeEngine`、`RuntimeContext`、`ICompileContext`、`IRuntimeContext`、`ICompileTimeRouter`、`RouterCompileMode`、`IGroupData`、`IRedirectable` |
| `VeloxDev.MVVM` | `[VeloxProperty]`、`[VeloxCommand]` |

**预期结果：** 每一行都对应真实命名空间 —— 新工程的组件文件里 `using VeloxDev.WorkflowSystem;`、`using VeloxDev.Core.WorkflowSystem.CompilerEx;`、`using VeloxDev.MVVM;` 都能编译。
