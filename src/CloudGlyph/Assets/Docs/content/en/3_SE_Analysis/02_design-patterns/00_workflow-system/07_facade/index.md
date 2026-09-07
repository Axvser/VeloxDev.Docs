# Workflow System — Design Patterns — Facade

`WorkflowBuilder` is a single façade over the whole component system: four nested attribute types declare which Helper each component type uses, the concurrency cap of the receive task, the virtual-link/slot type, and so on — and the source generator produces the rest of the component surface. Each attribute is generic over its matching helper-interface constraint, so a wrong Helper type is rejected at compile time.

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`, lines 3-49

```csharp
public sealed class WorkflowBuilder
{
    // ... TreeAttribute<T : IWorkflowTreeViewModelHelper, new()> ...
    // ... NodeAttribute<T : IWorkflowNodeViewModelHelper, new()>(int workSemaphore = 1) ...
    // ... SlotAttribute<T : IWorkflowSlotViewModelHelper, new()> ...
    // ... LinkAttribute<T : IWorkflowLinkViewModelHelper, new()>(Type? slotType = default) ...
}
```

| Attribute | Helper constraint | Extra surface it selects |
|---|---|---|
| `TreeAttribute<T>` | `IWorkflowTreeViewModelHelper` | `VirtualLinkType`, `VirtualSlotType` |
| `NodeAttribute<T>` | `IWorkflowNodeViewModelHelper` | `workSemaphore` (receive-task concurrency cap) |
| `SlotAttribute<T>` | `IWorkflowSlotViewModelHelper` | — |
| `LinkAttribute<T>` | `IWorkflowLinkViewModelHelper` | `slotType` (initial slot type) |

Demo usage is one line per component type, e.g. `[WorkflowBuilder.Node<EnumSelectorHelper>(workSemaphore: 1)]` on `EnumSelectorNodeViewModel`. The default components (`TreeDefaultViewModel`, `NodeDefaultViewModel`, `SlotDefaultViewModel`, `LinkDefaultViewModel`) ship under `Templates/ViewModels/*.cs`.
