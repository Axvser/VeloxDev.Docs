# 工作流系统 — 设计模式 — 模式总览

下表中的每个模式都落在当前源码上；每个专页都给出带文件路径与行范围的代码片段。

| 模式 | 位置 | 关键成员 | 源码 |
|---|---|---|---|
| 1. 模板方法 | 组件 Helper | `TreeHelper<T>.Install/Uninstall/Closing/CloseAsync/Closed`、`CreateLink`、`ValidateConnection`；`NodeHelper<T>` 骨架（`ReceiveAsync`/`AccessAsync` 默认实现） | `Templates/Helpers/TreeHelper.cs`、`Templates/Helpers/NodeHelper.cs` |
| 2. 命令 | `IVeloxCommand` + 撤销/重做栈 | `StandardCreateNode`、`StandardSubmit`、`StandardUndo`、`StandardRedo`、`WorkflowActionPair` | `StandardEx/WorkflowTreeEx.cs` |
| 3. 观察者 | Helper 集合事件 + `PropertyChanged` | `TreeHelper.OnNodesChanged/OnLinksChanged` → `NodeAdded`/`LinkAdded`；`EnumSelectorNodeViewModel.OnOutputSlotsPropertyChanged` | `Templates/Helpers/TreeHelper.cs`、`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs` |
| 4. 策略 | 输出槽选择 + 编译期路由解析 | `SlotEnumerator.SetSelector/TrySelect`；`ICompileTimeRouter.GetRouteTable`/`ResolveRouteKey`；`RouterCompileMode` | `SelectorEx/SlotEnumerator.cs`、`CompilerEx/Compile/Contracts/ICompileTimeRouter.cs`、`CompilerEx/Compile/Contracts/RouterCompileMode.cs` |
| 5. 代理 / 装饰器 | 源生成 partial ViewModel | `[WorkflowBuilder.*]`；转发给 Helper 的命令包装（`NodeDefaultViewModel.Receive`） | `Templates/WorkflowBuilder.cs`、`Templates/ViewModels/NodeDefaultViewModel.cs` |
| 6. 外观 | `WorkflowBuilder` 嵌套特性类型 | `TreeAttribute<T>`、`NodeAttribute<T>`、`SlotAttribute<T>`、`LinkAttribute<T>` | `Templates/WorkflowBuilder.cs` |
| 7. 组合 | 节点包含槽；连线派生为节点对 | `IWorkflowNodeViewModel.Slots`、`WorkflowSpatialManager.InsertLink`（`NodePairBoundsProvider`） | `Interfaces/WorkflowSystem/Components/IWorkflowNodeViewModel.cs`、`GUI/Virtualization/WorkflowSpatialManager.cs` |
| 8. 虚拟代理 | 空间虚拟化 | `WorkflowSpatialEx.Virtualize`（public）/ `VirtualizeCore`（private）、`TreeHelper.OnViewportChanged`、`EnableMap` | `GUI/Virtualization/WorkflowSpatialEx.cs`、`Templates/Helpers/TreeHelper.cs` |
| 9. 策略（运行时） | 重定向 / 回退到更早的编译状态 | `IRedirectable.ResolveRedirectAsync`、`RuntimeEngine.RunAsync`（朝目标 Order 重跑整图） | `CompilerEx/Runtime/Contracts/IRedirectable.cs`、`CompilerEx/Runtime/RuntimeEngine.cs` |
| 10. 策略族 + 空对象 | 2026-09-27 的宿主接缝：闸门、观察者、重试、错误接收器、补偿、检查点存储、日志写入器 | `IExecutionGate` / `IExecutionObserver` / `INodeRetryPolicy` / `IExecutionErrorSink` / `IExecutionCompensation` / `IExecutionCheckpointStore` / `ILogWriter`，每项都有 `Delegate*` 或具体实现，每项默认 `null` | `CompilerEx/Runtime/Contracts/*.cs`、`CompilerEx/Runtime/Model/*.cs`、`RuntimeEngine.Session()` |
| 11. 备忘录 | 运行位置作为快照，由 caretaker 只存不看 | `ExecutionCheckpoint`、`RuntimeContext.Snapshot`（internal）、`RuntimeEngine.Restore` / `RequireSameShape`、`ExecutionCheckpoint.Rekey`、`InMemoryCheckpointStore`、`FileCheckpointStore` | `CompilerEx/Runtime/Model/ExecutionCheckpoints.cs`、`Runtime/RuntimeEngine.cs`、`VeloxDev.Core.Extension/CheckpointEx.cs` |
| 12. 适配器（委托） | 把 lambda 变成契约实现 | `DelegateExecutionGate`、`DelegateExecutionObserver`、`DelegateExecutionErrorSink`、`DelegateExecutionCompensation`、`DelegateLogWriter` | `CompilerEx/Runtime/Model/` —— `ExecutionGates.cs`、`ExecutionObservers.cs`、`ErrorSinks.cs`、`Compensations.cs`、`LogWriters.cs` |
| 13. 规则链 + 宿主策略钩子 | 连接拖拽预览与完成共用规则集；宿主只能收紧 | `StandardCheckConnection`、`ConnectionCheck`、`WorkflowInput.PreviewValidating`、`StandardSetPreviewReceiver`、`StandardRefreshConnectionPreview` | `StandardEx/WorkflowTreeEx.cs`、`Interfaces/WorkflowSystem/Connections/ConnectionCheck.cs`、`GUI/Events/WorkflowInput.cs` |
