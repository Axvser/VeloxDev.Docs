# Workflow System — Design Patterns — Facade

The `WorkflowBuilder` nested attribute types (`TreeAttribute<T>`, `NodeAttribute<T>`, `SlotAttribute<T>`, `LinkAttribute<T>`) form a compact façade over the whole component system: one attribute selects helper type, concurrency, virtual-link type, etc., and the source generator produces the rest. All four require the matching helper interface constraint (`IWorkflowTreeViewModelHelper`, `IWorkflowNodeViewModelHelper`, …).

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`, lines 3-50.
