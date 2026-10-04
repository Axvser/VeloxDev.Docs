# Workflow System — 验证与运行声明

## 1. 对照真实仓库的验证

- **编译 / 运行时测试** —— `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`：
    `CompileDecompositionTests.cs`（分段形状）、`RuntimeEngineRunTests.cs`（链上数据流、动态路由、扇出、`IGroupData` 汇合、终结分支、错误停止）、`RuntimeRedirectTests.cs`（重定向契约、50 次上限）、`EntrySemanticsTests.cs`（三个入口）、`CompileToReverseTests.cs`（Terminal / 祖先锥 / 不伪造结果的规矩）、`EngineHostContractFailureTests.cs`（路由器 / 重定向 / attach 抛出会结束整轮，而不是让会话看起来还在 `"Running"`）。
- **宿主能力测试** —— `ExecutionGateTests.cs`、`ExecutionObserverTests.cs`、`ExecutionRetryTests.cs`、`ExecutionErrorSinkTests.cs`、`ExecutionCompensationTests.cs`、`ExecutionCheckpointTests.cs`、`CompilerLogWriterTests.cs`、`RuntimeContextLogConcurrencyTests.cs`、`NodeReportTests.cs`、`ParallelExecutionTests.cs`、`CompiledOutlineTests.cs`。
- **值类型 / 拓扑测试** —— `Src/Core/VeloxDev.Core.Test/WorkflowSystem/`（`AnchorTests`、`SlotEnumeratorTests`、`WorkflowTreeExTests` 等）。
- **序列化测试** —— `Src/Core/VeloxDev.Core.Extension.Test/Serialization/ComponentModelExTests.cs`、`ExecutionCheckpointSerializationTests.cs`。
- **Demo** —— `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 搭出完整的电压分析链（`Controller → Timer → Generate Dataset → [Stats, Dist, Anomaly] → Merge Report (IGroupData) → Enum Selector → [Report High/Low/Zero]`），并在 `ConfigureRun` 里配置**全部七项**宿主能力。每个完整版平台 demo 都把它接到运行 / 恢复 / 停止 / 暂停 /「从检查点继续」上。
    注意：同级的 `* Trimmed` demo 是**只有节点编辑器**的 —— 它们既不引用 `Common/Lib`，也不引用编译器/运行时。它们是*编辑器*面在裁剪安全上的权威 demo，不是本特性编译执行层的。

## 2. 运行声明

- ✅ **2026-10-01 真实构建并运行。** 命令：在一个控制台项目里 `dotnet build -c Debug` 然后 `dotnet run -c Debug`（`net10.0`，启用 `Nullable` 与 `ImplicitUsings`），项目引用 `Src/Core/VeloxDev.Core`、`Src/Core/VeloxDev.Core.Extension` 与 `Src/Generators/VeloxDev.Core.Generator`（最后一个以 `ReferenceOutputAssembly=false` 作为 analyzer），.NET SDK 10.0.401。程序就是 `07_完整代码` 里全文给出的那个，加上它点名的各组件文件。

  实测输出：

```text
[1] Nodes=3 Links=2
[2] root: Completed data=tick->bias->print attempt=1 outcome=Completed
[2] orders: 0,1,2
[2] entries=1 first=ChainSegment
[2] outline: Execute | TickerNode → BiasNode → PrinterNode
[3] result: Completed data=tick->bias reached=True
[4] copy: Nodes=3 Links=2 Completed data=tick->bias->print
[5] paused: status=Paused isPaused=True running=True data=<null>
[5] resumed: status=Completed data=tick->bias->print outcome=Completed
[6] observed: NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
[6] sink on a clean run: 0 records
[7] checkpoint: attempt=1 outputs=1 shape=<三个 RuntimeId GUID>
[7] resume: status=Completed data=tick->bias->print outcome=Completed
[7] refused on a serialized copy: The checkpoint does not belong to this graph status=Idle
[8] retry: status=Completed data=ok drives=3 attempt=1 outcome=Completed
[8] retry logs: 01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
[9] logfile: fileLines=3 retained=2 snapshot=2
[9] retained: 02. BiasNode | 03. PrinterNode
[9] file head: 01. TickerNode
[10] compensate: status=Stopped outcome=Failed currentOrder=-1 reversed=[BoomNode]
[11] segments: ChainSegment, ParallelSegment
[11] MaxParallelBranches=null: overlap=True
[11] MaxParallelBranches=1:    overlap=False
```

  每一行都与它所属步骤写明的**预期结果**一致。有三行值得再看一遍：

  - `[8] … attempt=1` —— 重试**不是**一趟过图，所以产物登记表的趟戳不动，汇合聚合因此仍然正确。
  - `[7] … refused … status=Idle` —— 恢复在*碰会话之前*就被拒绝，所以 `Status` 仍读作 `Idle`，而不是谎称跑过一场。
  - `[11] … overlap=True` / `overlap=False` —— 扇出默认真的并发，上限为 1 时真的串行。

- ✅ **也由随库测试套件验证**（读而非重跑）：上述每条契约都由第 1 节点名的测试钉住，其中包括 `MaxParallelBranches` 上限与 `MaxRetainedLogs` 行为 —— 这两项没有 demo 覆盖。
- ⚠️ **未通过运行 GUI 宿主验证。** 各平台 demo（`Examples/Workflow/WPF/Demo`、`Avalonia/Demo`、`Blazor/Demo`、`MAUI/Demo`、`WinUI/Demo`、`WinForms/Demo`、`Jalium/Demo`）**没有**被构建或启动 —— 它们是 GUI 宿主（WPF 是 `net9.0-windows`，Avalonia 是 `net8.0`，另有 MAUI/WinUI/Blazor 工作负载）。这些页面上关于它们的说法读自源码，而不是来自运行中的应用。请把「真实仓库里它在哪」当作源码核实，而不是运行核实。
- ⚠️ **一处无法钉死的说法。** 快速开始把各组件拆成独立文件，这是实测构建所采用的形式（也是 demo 仓库的做法）。另做的一次探针把两个生成组件放在**同一个**文件里，也编译通过，所以「一个组件一个文件」是 demo 的约定，而不是生成器的硬性要求；把*整个*程序塞进一个文件的形式没有重新验证。
