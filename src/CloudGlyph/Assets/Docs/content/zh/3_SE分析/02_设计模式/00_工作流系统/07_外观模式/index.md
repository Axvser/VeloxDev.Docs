# 工作流系统 — 设计模式 — 外观模式

`WorkflowBuilder` 是整个组件系统的单一门面：四个嵌套特性类型声明每种组件使用哪个 Helper、接收任务的并发上限、虚拟连线/槽类型等等 —— 其余组件表面由源生成器产出。每个特性都以对应的 helper 接口约束为泛型约束，所以错误的 Helper 类型在编译期就被拒绝。

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`，3-49 行

```csharp
public sealed class WorkflowBuilder
{
    // ... TreeAttribute<T : IWorkflowTreeViewModelHelper, new()> ...
    // ... NodeAttribute<T : IWorkflowNodeViewModelHelper, new()>(int workSemaphore = 1) ...
    // ... SlotAttribute<T : IWorkflowSlotViewModelHelper, new()> ...
    // ... LinkAttribute<T : IWorkflowLinkViewModelHelper, new()>(Type? slotType = default) ...
}
```

| 特性 | Helper 约束 | 它选择的额外表面 |
|---|---|---|
| `TreeAttribute<T>` | `IWorkflowTreeViewModelHelper` | `VirtualLinkType`、`VirtualSlotType` |
| `NodeAttribute<T>` | `IWorkflowNodeViewModelHelper` | `workSemaphore`（接收任务并发上限） |
| `SlotAttribute<T>` | `IWorkflowSlotViewModelHelper` | — |
| `LinkAttribute<T>` | `IWorkflowLinkViewModelHelper` | `slotType`（初始槽类型） |

demo 用法是每种组件一行，例如 `EnumSelectorNodeViewModel` 上的 `[WorkflowBuilder.Node<EnumSelectorHelper>(workSemaphore: 1)]`。默认组件（`TreeDefaultViewModel`、`NodeDefaultViewModel`、`SlotDefaultViewModel`、`LinkDefaultViewModel`）位于 `Templates/ViewModels/*.cs`。
