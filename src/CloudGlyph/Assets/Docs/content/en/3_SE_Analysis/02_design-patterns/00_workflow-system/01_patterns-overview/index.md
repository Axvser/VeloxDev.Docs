# Workflow System — Design Patterns — Patterns Overview

| Pattern | Where | Key members | Source |
|---|---|---|---|
| 1. Template Method | Component helpers | `TreeHelper<T>.Install/Uninstall/CloseAsync`, `CreateLink`, `ValidateConnection`, `SendConnection` | `Templates/Helpers/*.cs` |
| 2. Command | `IVeloxCommand` + undo/redo stacks | `StandardCreateNode`, `StandardSubmit`, `StandardUndo`, `StandardRedo` | `StandardEx/WorkflowTreeEx.cs` |
| 3. Observer | `ObservableCollection` + command events | `TreeHelper.OnNodesChanged`, `SlotHelper.OnTargetsChanged`, `HttpHelper` `ReceiveCommand` events | `Templates/Helpers/*.cs`, `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/HttpHelper.cs` |
| 4. Strategy | `SlotEnumerator` + `ICompileTimeRouter` | `SetSelector`, `GetRouteTable`, `ResolveRouteKey`, `RouterCompileMode` | `SelectorEx/SlotEnumerator.cs`, `CompilerEx/ICompileTimeRouter.cs`, `RouterCompileMode.cs` |
| 5. Proxy / Decorator | Source-generated partial ViewModels | `[WorkflowBuilder.*]` + Helper injection | `Templates/WorkflowBuilder.cs`, `Templates/ViewModels/*.cs` |
| 6. Facade | `WorkflowBuilder` | `TreeAttribute<T>`, `NodeAttribute<T>`, `SlotAttribute<T>`, `LinkAttribute<T>` | `Templates/WorkflowBuilder.cs` |
| 7. Composition | Node contains slots; links derived | `IWorkflowNodeViewModel.Slots`, `WorkflowSpatialManager.InsertLink` | `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`, `WorkflowSystem/WorkflowSpatialManager.cs` |
| 8. Virtual Proxy | Spatial virtualization | `WorkflowSpatialEx.Virtualize`, `TreeHelper.Viewport` | `StandardEx/WorkflowSpatialEx.cs` |
| 9. Strategy (runtime) | Redirect / error handling | `IRedirectable.ResolveRedirectAsync`, `CompilerEngine.RunAsync` | `CompilerEx/IRedirectable.cs`, `CompilerEngine.cs` |
