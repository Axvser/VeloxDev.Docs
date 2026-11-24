# 工作流自动布局

`Arrange` 为整棵树或一个节点可达的子图求解布局，并以一步可撤销操作写回。默认求解器先把每个层级对齐到父节点中心，再分离重叠的瓦片。

- [布局入口](00_布局入口/index.md) — `WorkflowLayoutEx`、`WorkflowLayoutOptions`、遍历方式与结果。
- [布局快照](01_布局快照/index.md) — `WorkflowLayoutProblem`、其构建器、可变状态与执行上下文。
- [布局解](02_布局解/index.md) — 放置、成本、位置决策与容差策略。
- [管线与求解器](03_管线与求解器/index.md) — 求解器/规划器/阶段/应用器扩展缝与默认实现。

```csharp
var result = node.Arrange(new WorkflowLayoutOptions { RowGap = 10, ColumnGap = 64 });
Console.WriteLine($"{result.Applied} {result.AppliedCount}");

tree.GetHelper().Undo();   // 一步恢复每个锚点
```

命名空间：`VeloxDev.WorkflowSystem`（程序集 `VeloxDev.Core`）。布局在模型上工作，不涉及适配器或视图。任务式教程见[工作流自动布局](../../1_快速开始/06_工作流自动布局/index.md)。
