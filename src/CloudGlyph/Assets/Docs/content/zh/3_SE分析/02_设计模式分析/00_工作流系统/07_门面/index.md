# Workflow System — 设计模式 — 门面

`WorkflowBuilder` 是整个组件系统的单一门面：四个嵌套属性类型声明每个组件类型使用哪个 Helper、接收任务的并发上限、虚拟连接/槽类型等——源生成器负责生成组件表面的其余部分。每个属性都对其匹配的 Helper 接口约束做泛型 `where T : …Helper, new()`，Helper 类型写错会在编译期被拒绝：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`，第 3-50 行

```csharp
public sealed class WorkflowBuilder
{
    [AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public sealed class TreeAttribute<T>(Type? virtualLinkType = default, Type? virtualSlotType = default) : Attribute
        where T : IWorkflowTreeViewModelHelper, new()
    {
        public Type? VirtualLinkType { get; } = virtualLinkType;
        public Type? VirtualSlotType { get; } = virtualSlotType;
    }

    [AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public sealed class NodeAttribute<T>(int workSemaphore = 1) : Attribute
        where T : IWorkflowNodeViewModelHelper, new()
    {
        public int Semaphore { get; } = workSemaphore;
    }

    [AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public sealed class SlotAttribute<T> : Attribute
        where T : IWorkflowSlotViewModelHelper, new();

    [AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public sealed class LinkAttribute<T>(Type? slotType = default) : Attribute
        where T : IWorkflowLinkViewModelHelper, new()
    {
        public Type? SlotType { get; } = slotType;
    }
}
```

| 属性 | Helper 约束 | 额外选择的表面 |
|---|---|---|
| `TreeAttribute<T>` | `IWorkflowTreeViewModelHelper` | `VirtualLinkType`、`VirtualSlotType` |
| `NodeAttribute<T>` | `IWorkflowNodeViewModelHelper` | `workSemaphore`（接收任务并发上限） |
| `SlotAttribute<T>` | `IWorkflowSlotViewModelHelper` | — |
| `LinkAttribute<T>` | `IWorkflowLinkViewModelHelper` | `slotType`（初始槽类型） |

演示用法每组件类型一行，如 `ControllerViewModel` 上的 `[WorkflowBuilder.Node<NodeHelper>]`、`EnumSelectorNodeViewModel` 上的 `[WorkflowBuilder.Node<EnumSelectorHelper>]`。默认组件（`TreeDefaultViewModel`、`NodeDefaultViewModel`、`SlotDefaultViewModel`、`LinkDefaultViewModel`）不带这些属性，直接以 `Templates/ViewModels/*.cs` 的默认 Helper 实例（`new TreeHelper()` 等）装配。
