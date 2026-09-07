# Workflow System — Design Patterns — Patterns Overview

Every pattern below is grounded in the current source; each dedicated page carries the code snippet with its file path and line range.

| Pattern | Where | Key members | Source |
|---|---|---|---|
| 1. Template Method | Component helpers | `TreeHelper<T>.Install/Uninstall/Closing/CloseAsync/Closed`, `CreateLink`, `ValidateConnection`; `NodeHelper<T>` skeleton (`ReceiveAsync`/`AccessAsync` defaults) | `Templates/Helpers/TreeHelper.cs`, `Templates/Helpers/NodeHelper.cs` |
| 2. Command | `IVeloxCommand` + undo/redo stacks | `StandardCreateNode`, `StandardSubmit`, `StandardUndo`, `StandardRedo`, `WorkflowActionPair` | `StandardEx/WorkflowTreeEx.cs` |
| 3. Observer | Helper collection events + `PropertyChanged` | `TreeHelper.OnNodesChanged/OnLinksChanged` → `NodeAdded`/`LinkAdded`; `EnumSelectorNodeViewModel.OnOutputSlotsPropertyChanged` | `Templates/Helpers/TreeHelper.cs`, `Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs` |
| 4. Strategy | Output-slot selection + compile-time route resolution | `SlotEnumerator.SetSelector/TrySelect`; `ICompileTimeRouter.GetRouteTable`/`ResolveRouteKey`; `RouterCompileMode` | `SelectorEx/SlotEnumerator.cs`, `CompilerEx/Compile/Contracts/ICompileTimeRouter.cs`, `CompilerEx/Compile/Contracts/RouterCompileMode.cs` |
| 5. Proxy / Decorator | Source-generated partial ViewModels | `[WorkflowBuilder.*]`; command wrappers that forward to the Helper (`NodeDefaultViewModel.Receive`) | `Templates/WorkflowBuilder.cs`, `Templates/ViewModels/NodeDefaultViewModel.cs` |
| 6. Facade | `WorkflowBuilder` nested attribute types | `TreeAttribute<T>`, `NodeAttribute<T>`, `SlotAttribute<T>`, `LinkAttribute<T>` | `Templates/WorkflowBuilder.cs` |
| 7. Composition | Node contains slots; links derived as node pairs | `IWorkflowNodeViewModel.Slots`, `WorkflowSpatialManager.InsertLink` (`NodePairBoundsProvider`) | `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`, `GUI/Virtualization/WorkflowSpatialManager.cs` |
| 8. Virtual Proxy | Spatial virtualization | `WorkflowSpatialEx.Virtualize`/`VirtualizeCore`, `TreeHelper.OnViewportChanged`, `EnableMap` | `StandardEx/WorkflowSpatialEx.cs`, `Templates/Helpers/TreeHelper.cs` |
| 9. Strategy (runtime) | Redirect / fall-back to an earlier compile state | `IRedirectable.ResolveRedirectAsync`, `RuntimeEngine.RunAsync` (whole-graph re-run toward the target Order) | `CompilerEx/Runtime/Contracts/IRedirectable.cs`, `CompilerEx/Runtime/RuntimeEngine.cs` |
