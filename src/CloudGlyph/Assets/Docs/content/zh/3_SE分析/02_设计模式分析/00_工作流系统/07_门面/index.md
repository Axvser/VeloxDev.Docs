# Workflow System — 设计模式 — 门面

`WorkflowBuilder` 的嵌套属性类型（`TreeAttribute<T>`、`NodeAttribute<T>`、`SlotAttribute<T>`、`LinkAttribute<T>`）构成整个组件系统的紧凑门面：一个属性选择 Helper 类型、并发度、虚拟连接类型等，源生成器生成其余部分。四个属性都要求对应的 Helper 接口约束（`IWorkflowTreeViewModelHelper`、`IWorkflowNodeViewModelHelper` 等）。

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`，第 3-50 行。
