# Workflow System — 设计模式 — 模式总览

下表每一条都立足于当前源码；各专题页附有带源码路径与行范围的代码摘录。

| 模式 | 位置 | 关键成员 | 源码 |
|---|---|---|---|
| 1. 模板方法 | 组件 Helper | `TreeHelper<T>.Install/Uninstall/Closing/CloseAsync/Closed`、`CreateLink`、`ValidateConnection`；`NodeHelper<T>` 骨架（`ReceiveAsync`/`AccessAsync` 默认实现） | `Templates/Helpers/TreeHelper.cs`、`Templates/Helpers/NodeHelper.cs` |
| 2. 命令 | `IVeloxCommand` + 撤销/重做栈 | `StandardCreateNode`、`StandardSubmit`、`StandardUndo`、`StandardRedo`、`WorkflowActionPair` | `StandardEx/WorkflowTreeEx.cs` |
| 3. 观察者 | Helper 集合事件 + `PropertyChanged` | `TreeHelper.OnNodesChanged/OnLinksChanged` → `NodeAdded`/`LinkAdded`；`EnumSelectorNodeViewModel.OnOutputSlotsPropertyChanged` | `Templates/Helpers/TreeHelper.cs`、`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs` |
| 4. 策略 | 输出槽选择 + 编译期路由解析 | `SlotEnumerator.SetSelector/TrySelect`；`ICompileTimeRouter.GetRouteTable`/`ResolveRouteKey`；`RouterCompileMode` | `SelectorEx/SlotEnumerator.cs`、`CompilerEx/Compile/Contracts/ICompileTimeRouter.cs`、`RouterCompileMode.cs` |
| 5. 代理 / 装饰器 | 源生成的 partial ViewModel | `[WorkflowBuilder.*]`；转发到 Helper 的命令包装（`NodeDefaultViewModel.Receive`） | `Templates/WorkflowBuilder.cs`、`Templates/ViewModels/NodeDefaultViewModel.cs` |
| 6. 门面 | `WorkflowBuilder` 嵌套属性类型 | `TreeAttribute<T>`、`NodeAttribute<T>`、`SlotAttribute<T>`、`LinkAttribute<T>` | `Templates/WorkflowBuilder.cs` |
| 7. 组合 | 节点包含槽位；连接以节点对派生 | `IWorkflowNodeViewModel.Slots`、`WorkflowSpatialManager.InsertLink`（`NodePairBoundsProvider`） | `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`、`GUI/Virtualization/WorkflowSpatialManager.cs` |
| 8. 虚拟代理 | 空间虚拟化 | `WorkflowSpatialEx.Virtualize`/`VirtualizeCore`、`TreeHelper.OnViewportChanged`、`EnableMap` | `GUI/Virtualization/WorkflowSpatialEx.cs`、`Templates/Helpers/TreeHelper.cs` |
| 9. 策略（运行期） | 重定向 / 回退到更早的编译状态 | `IRedirectable.ResolveRedirectAsync`、`RuntimeEngine.RunAsync`（朝向目标 Order 的整图重跑） | `CompilerEx/Runtime/Contracts/IRedirectable.cs`、`CompilerEx/Runtime/RuntimeEngine.cs` |

注：`WorkflowSpatialEx` 命名空间虽为 `VeloxDev.WorkflowSystem.StandardEx`，物理文件在 `WorkflowSystem/GUI/Virtualization/`。
