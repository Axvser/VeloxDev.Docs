# Workflow System — 设计模式 — Patterns Overview

| 模式 | 位置 | 关键成员 | 源码 |
|---|---|---|---|
| 1. 模板方法 | 组件 Helper | `TreeHelper<T>.Install/Uninstall/CloseAsync`、`CreateLink`、`ValidateConnection`、`SendConnection` | `Templates/Helpers/*.cs` |
| 2. 命令 | `IVeloxCommand` + 撤销/重做栈 | `StandardCreateNode`、`StandardSubmit`、`StandardUndo`、`StandardRedo` | `StandardEx/WorkflowTreeEx.cs` |
| 3. 观察者 | `ObservableCollection` + 命令事件 | `TreeHelper.OnNodesChanged`、`SlotHelper.OnTargetsChanged`、`HttpHelper` 的 `ReceiveCommand` 事件 | `Templates/Helpers/*.cs`、`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/HttpHelper.cs` |
| 4. 策略 | `SlotEnumerator` + `ICompileTimeRouter` | `SetSelector`、`GetRouteTable`、`ResolveRouteKey`、`RouterCompileMode` | `SelectorEx/SlotEnumerator.cs`、`CompilerEx/ICompileTimeRouter.cs`、`RouterCompileMode.cs` |
| 5. 代理 / 装饰器 | 源生成的 partial ViewModel | `[WorkflowBuilder.*]` + Helper 注入 | `Templates/WorkflowBuilder.cs`、`Templates/ViewModels/*.cs` |
| 6. 门面 | `WorkflowBuilder` | `TreeAttribute<T>`、`NodeAttribute<T>`、`SlotAttribute<T>`、`LinkAttribute<T>` | `Templates/WorkflowBuilder.cs` |
| 7. 组合 | 节点包含槽位；连接由槽位派生 | `IWorkflowNodeViewModel.Slots`、`WorkflowSpatialManager.InsertLink` | `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`、`WorkflowSystem/WorkflowSpatialManager.cs` |
| 8. 虚拟代理 | 空间虚拟化 | `WorkflowSpatialEx.Virtualize`、`TreeHelper.Viewport` | `StandardEx/WorkflowSpatialEx.cs` |
| 9. 策略（运行期） | 重定向 / 错误处理 | `IRedirectable.ResolveRedirectAsync`、`CompilerEngine.RunAsync` | `CompilerEx/IRedirectable.cs`、`CompilerEngine.cs` |
