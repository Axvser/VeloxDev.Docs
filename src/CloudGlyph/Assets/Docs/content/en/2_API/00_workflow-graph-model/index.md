# Workflow graph model

The graph model lives in `VeloxDev.Core`, namespace `VeloxDev.WorkflowSystem`. A tree owns nodes, a node owns slots, and a link joins a sender slot to a receiver slot. Each of the four roles is an interface, a default view model, and a helper that carries its behaviour.

The pages below split the surface by role:

- [Component contracts](00_components/index.md) — the four component interfaces, the helper contracts and the shared lifecycle members.
- [Default view models](01_default-view-models/index.md) — the generated component attributes and the four sealed default implementations.
- [Helpers](02_helpers/index.md) — `TreeHelper<T>`, `NodeHelper<T>`, `SlotHelper<T>` and `LinkHelper<T>`.
- [Geometry models](03_geometry/index.md) — `Anchor`, `Size`, `Offset`, `Scale`, `CanvasLayout`, `Viewport`, `ZoomCenter` and `WorkflowBounds`.

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

Console.WriteLine($"{tree.Nodes.Count} {node.Slots.Count} {node.GetWorldAnchor()}");
```

The generated component path (`[WorkflowBuilder.*]` plus `InitializeWorkflow`) is what most hosts use; the default view models are the concrete types the generator's helpers instantiate when no custom type is supplied. For a task-oriented walkthrough, see [Workflow graph model](../../1_QuickStart/00_workflow-graph-model/index.md).
