# Workflow auto-layout

`Arrange` solves a layout for a tree or for the subgraph reachable from one node and writes the result back as one undoable action. The default solver aligns each hierarchy to its parent's centre, then separates overlapping tiles.

- [Layout entry](00_layout-entry/index.md) — `WorkflowLayoutEx`, `WorkflowLayoutOptions`, traversal and the result.
- [Layout snapshot](01_layout-snapshot/index.md) — `WorkflowLayoutProblem`, its builder, the mutable state and the execution context.
- [Layout solution](02_layout-solution/index.md) — placements, cost, position decisions and the tolerance policy.
- [Pipeline and solver](03_pipeline-and-solver/index.md) — the solver/planner/stage/applier seams and the default implementations.

```csharp
var result = node.Arrange(new WorkflowLayoutOptions { RowGap = 10, ColumnGap = 64 });
Console.WriteLine($"{result.Applied} {result.AppliedCount}");

tree.GetHelper().Undo();   // one step restores every anchor
```

Namespace: `VeloxDev.WorkflowSystem` in `VeloxDev.Core`. Layout works on the model; no adapter or view is involved. For a task-oriented walkthrough, see [Workflow auto-layout](../../1_QuickStart/06_workflow-auto-layout/index.md).
