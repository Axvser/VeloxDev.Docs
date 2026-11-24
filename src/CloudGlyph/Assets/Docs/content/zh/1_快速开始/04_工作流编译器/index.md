# 工作流编译器

`CompilerViewModel` 把从某个节点可达的图变成 `CompiledGraph`：一组有序的 `ChainSegment`、`BranchSegment` 与 `ParallelSegment`。编译产物描述所有可能的执行并固定每个节点的编译序号，本身不运行任何东西。

两个角色决定遍历方向：

- `CompileRole.Root` 从起始节点向下游编译可达子图。
- `CompileRole.Terminal` 向上游走，只编译计算某个节点所需的祖先锥。

下面两页分别用真实图构建这两个角色：

- [根节点编译](00_根节点编译/index.md)——链、扇出、汇合、编译序号与扁平大纲。
- [分支与终止编译](01_分支与终止编译/index.md)——路由器、静态剪枝、并行段与反向编译。

编译器位于 `VeloxDev.Core.WorkflowSystem.CompilerEx`，属于 `VeloxDev.Core`。除图模型页的前置条件外不需要额外包。
