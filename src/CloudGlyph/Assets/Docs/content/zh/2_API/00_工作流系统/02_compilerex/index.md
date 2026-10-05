# 工作流系统 — 命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`

编译/运行管线。`CompilerViewModel.CompileAsync` 把从某个节点可达的子图分解成无环的编译产物（`CompiledGraph`，由 `ChainSegment` / `BranchSegment` / `ParallelSegment` 组成），并给每个 `ICompileTimeAware` 节点一个编译身份（`CompileContext`）；随后 `RuntimeEngine.RunAsync` 驱动这些分段，通过节点唯一的执行入口 `IWorkflowNodeViewModelHelper.ReceiveAsync` 调用它。

本命名空间内的类型全部是 `public`。只有两个类型是刻意 `internal` 的 —— `BranchRuntimeContext` 与 `CompileKeyNormalizer` —— 它们出现在哪个页面就在哪个页面标注为 *internal*，因为它们解释了否则不可见的行为。

## 分节

命名空间太大，本页只作总览。它拆成五个子页：

| 页面 | 内容 |
|---|---|
| [编译管线](00_编译管线/index.md) | `CompilerViewModel`、`CompileRole`、编译模型（`CompiledGraph` / `CompileSegment` / `ChainSegment` / `BranchSegment` / `ParallelSegment` / `BranchOption`）、编译期契约（`ICompileContext` / `CompileContext` / `ICompileTimeAware` / `ICompileTimeRouter` / `RouterCompileMode`）、`CompiledOutline` |
| [运行时引擎](01_运行时引擎/index.md) | `RuntimeEngine.RunAsync`（含 `resumeFrom` 重载）、`IRuntimeContext`、`IRuntimeAware`、`IRedirectable`、`RunOutcome` |
| [会话：RuntimeContext 与 GroupData](01_运行时引擎/00_运行时上下文/index.md) | `RuntimeContext` 的全部成员（含宿主能力属性）与 `IGroupData` / `GroupData` |
| [执行契约](02_执行契约/index.md) | 宿主能力层：`IExecutionGate`、`IExecutionObserver`、`INodeRetryPolicy`、`IExecutionErrorSink`、`IExecutionCompensation`、`IExecutionCheckpointStore`、`ILogWriter` 及其记录/枚举载荷 |
| [执行实现](03_执行实现/index.md) | 这些契约的随库实现：`ManualExecutionGate`、`DelegateExecutionGate`、`DelegateExecutionObserver`、`DelegateExecutionErrorSink`、`DelegateExecutionCompensation`、`DelegateLogWriter`、`TextWriterLogWriter`、`ExponentialBackoffRetry` |
| [检查点](04_检查点/index.md) | `ExecutionCheckpoint`、`InMemoryCheckpointStore`、`BranchRuntimeContext`（internal），以及恢复/拒绝恢复的契约 |

序列化现在是一个独立特性，不再是工作流的子话题 —— 归档引擎（`VeloxDev.Serialization`）在 `VeloxDev.Core`；编译图与检查点文档（`CompiledGraphEx`、`CheckpointEx`、`FileCheckpointStore`）在同一命名空间下、位于 `VeloxDev.Core.Extension`。见 [序列化](../../09_序列化/index.md)。

> 关于「引擎驱动（Compiler）路径」与「节点驱动的广播路径」如何抵达**同一个** `ReceiveAsync` —— 入口、参数、时序 —— 见 [执行机制（Compiler 与 非Compiler）](../04_执行机制/index.md)。

## 证据

- **Demo** —— `Examples/Workflow/Common/Lib/ViewModels/Workflow/`（`WorkflowDemoSession.cs` 在同一个会话上配置全部七项宿主能力；`ControllerViewModel.cs` 先编译再驱动；`PythonScriptNodeViewModel.cs` 实现 `IRedirectable`），由 WPF / Avalonia / Blazor / MAUI / WinUI / WinForms / Jalium 完整版 demo 消费。
- **测试** —— `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`（`RuntimeEngineRunTests`、`RuntimeRedirectTests`、`ExecutionCheckpointTests`、`ExecutionCompensationTests`、`ExecutionErrorSinkTests`、`ExecutionGateTests`、`ExecutionObserverTests`、`ExecutionRetryTests`、`ParallelExecutionTests`、`CompilerLogWriterTests`、`RuntimeContextLogConcurrencyTests`、`NodeReportTests`、`EngineHostContractFailureTests`、`CompiledOutlineTests`、`EntrySemanticsTests`、`CompileDecompositionTests`、`CompileToReverseTests`，以及共用的 `ProbeGraph.cs` / `ProbeNodes.cs` 测试台）。

## 一段话讲清宿主能力层

在这一层出现之前，引擎对失败只有一种答案（重定向），而且没有任何接缝让宿主去持有、观察、重试、记录、撤销或恢复一次运行。它加了七个**可选**接缝 —— 暂停**门**、**观察者**、**重试策略**、**错误接收器**、**补偿器**、**检查点存储**与**日志写入器** —— 每一个都从宿主具体的 `RuntimeContext` 上读，每一个不设置时都逐字节复现之前的行为（连日志行数和驱动次数都一样）。它们经私有的 `Session()` 取用，因此在并行扇出**内部**同样有效；而其中大多数刻意**不**放进 `IRuntimeContext`，因为给那个接口加成员会破坏每一个外部实现。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/**`、`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/**`。*
