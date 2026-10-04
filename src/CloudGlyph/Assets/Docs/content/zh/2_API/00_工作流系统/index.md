# 工作流系统 — API 参考

`workflow-system` 特性的公开面，按命名空间分组，外加「关键成员契约」与「执行机制」两个横切页。下列每个类型都存在于真实源码中，并附源码路径。凡是从源码推断（而非 Demo/测试证据）得出的行为，都标注为*推断*。

## API — 分节

本特性的 API 参考拆成：

- [命名空间：VeloxDev.WorkflowSystem](00_workflowsystem/index.md) —— `VeloxDev.WorkflowSystem` 核心面（构建器特性、组件接口、几何/值类型、默认 ViewModel、选择器、空间索引、渲染就绪）
- [命名空间：VeloxDev.WorkflowSystem.StandardEx](01_standardex/index.md) —— `VeloxDev.WorkflowSystem.StandardEx` 标准行为扩展
- [命名空间：VeloxDev.Core.WorkflowSystem.CompilerEx](02_compilerex/index.md) —— `VeloxDev.Core.WorkflowSystem.CompilerEx` 的编译管线、编译模型、运行时引擎与宿主能力层
- [命名空间：VeloxDev.MVVM.Serialization](03_MVVM序列化/index.md) —— `VeloxDev.MVVM.Serialization`：`ComponentModelEx` 存取、`CompiledGraphEx`、`CheckpointEx` + `FileCheckpointStore`
- [关键成员契约](04_关键成员契约/index.md) —— 顶层 API 的条目模板式写法
- [执行机制（Compiler 与 非Compiler）](05_执行机制/index.md) —— Compiler（引擎驱动）与 非 Compiler（广播）两条路径如何抵达同一个 `ReceiveAsync`

### `compilerex` 内部

`VeloxDev.Core.WorkflowSystem.CompilerEx` 体量很大，所以它那页只是总览，下面是五个子页：

| 子页 | 内容 |
|---|---|
| [编译管线](02_compilerex/00_编译管线/index.md) | `CompilerViewModel`、`CompileRole`、`CompiledGraph` 与三种分段、`BranchOption`、编译期契约、`CompiledOutline` |
| [运行时引擎](02_compilerex/01_运行时引擎/index.md) | `RuntimeEngine.RunAsync`（含 `resumeFrom`）、`IRuntimeContext`、`IRuntimeAware`、`IRedirectable`、`RunOutcome` |
| [会话：RuntimeContext 与 GroupData](02_compilerex/01_运行时引擎/00_运行时上下文/index.md) | `RuntimeContext` 全部成员（含宿主能力属性）与 `IGroupData` / `GroupData` |
| [执行契约](02_compilerex/02_执行契约/index.md) | `IExecutionGate`、`IExecutionObserver`、`INodeRetryPolicy`、`IExecutionErrorSink`、`IExecutionCompensation`、`IExecutionCheckpointStore`、`ILogWriter` 及载荷类型 |
| [执行实现](02_compilerex/03_执行实现/index.md) | `ManualExecutionGate`、`Delegate*` 适配器、`TextWriterLogWriter`、`ExponentialBackoffRetry` |
| [检查点](02_compilerex/04_检查点/index.md) | `ExecutionCheckpoint`、`InMemoryCheckpointStore`、`BranchRuntimeContext`（internal） |

上面六条链接都可以从 [命名空间：VeloxDev.Core.WorkflowSystem.CompilerEx](02_compilerex/index.md) 这个命名空间总览页进入。

## 覆盖说明 —— 2026-09-27 的宿主能力层

编译/运行核心由 Demo + 测试证据完整覆盖。2026-09-27 新增的宿主能力层覆盖情况如下：

| 成员组 | 证据 |
|---|---|
| `IExecutionGate`、`IExecutionObserver`、`INodeRetryPolicy`、`IExecutionErrorSink`、`IExecutionCompensation`、`IExecutionCheckpointStore`、`ILogWriter` | **Demo** —— 七项全部由 `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 的 `ConfigureRun` 配在同一个会话上；以及**测试**（`CompilerEx/Execution*Tests.cs`、`CompilerLogWriterTests.cs`） |
| `MaxRetainedLogs`、`SnapshotLogs` | **仅测试**（`CompilerLogWriterTests.cs`、`RuntimeContextLogConcurrencyTests.cs`）——没有 demo 设置它们 |
| `MaxParallelBranches` | **仅测试**（`ParallelExecutionTests.cs`）——没有 demo 设置它，因此没有 demo 演示并发上限 |
| `Target` / `TargetReached` | **仅测试**（`CompileToReverseTests.cs`、`RuntimeEngineRunTests.cs`）——Agent 扩展会读它们，没有 demo 设置 `Target` |
| `RunOutcome`、`CompiledOutline` | **Demo**（`WorkflowDemoSession.cs` 读 `Outcome`；`TreeViewModel.cs` 绑定 `CompiledOutline.Of`）+ **测试** |

两个在行为上重要的 `internal` 类型 —— `BranchRuntimeContext` 与 `CompileKeyNormalizer` —— 都在它们出现的页面上被记录并标注为 `internal`，这样公开面就仍是对「调用方能调用什么」的精确陈述。
