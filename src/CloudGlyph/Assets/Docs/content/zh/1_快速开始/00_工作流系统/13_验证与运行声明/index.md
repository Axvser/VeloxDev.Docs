# 工作流系统 — 验证与运行声明

## 1. 对照真实仓库的验证

- **编译器 / 运行时测试** —— `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`：
  `CompileDecompositionTests.cs`（分段形状）、`RuntimeEngineRunTests.cs`（链式数据流、动态路由、扇出、`IGroupData` join、终端分支、错误停止）、`RuntimeRedirectTests.cs`（重定向契约、50 次重定向上限）、`EntrySemanticsTests.cs`（三个执行入口）、`CompileToReverseTests.cs`（Terminal / 祖先锥 / 不虚构规则）、`EngineHostContractFailureTests.cs`（抛异常的路由器 / 重定向 / attach 会结束运行，而不是让它看起来仍在 `"Running"`）。
- **宿主能力测试** —— `ExecutionGateTests.cs`、`ExecutionObserverTests.cs`、`ExecutionRetryTests.cs`、`ExecutionErrorSinkTests.cs`、`ExecutionCompensationTests.cs`、`ExecutionCheckpointTests.cs`、`CompilerLogWriterTests.cs`、`RuntimeContextLogConcurrencyTests.cs`、`NodeReportTests.cs`、`ParallelExecutionTests.cs`、`CompiledOutlineTests.cs`。
- **连接预览测试** —— `WorkflowConnectionPreviewTests.cs`（发送端 / 候选槽、`SlotState` 预览位、虚拟连线阶段、`PreviewValidating` 只能收紧、`StandardRefreshConnectionPreview`、`SlotHitTestEx`）。
- **值类型 / 拓扑测试** —— `Src/Core/VeloxDev.Core.Test/WorkflowSystem/`（`AnchorTests`、`SlotEnumeratorTests`、`WorkflowTreeExTests` 等）。
- **序列化测试** —— `Src/Core/VeloxDev.Core.Extension.Test/Serialization/ComponentModelExTests.cs`、`ExecutionCheckpointSerializationTests.cs`。
- **Demo** —— `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 构建完整的电压分析链（`Controller → Timer → Generate Dataset → [Stats, Dist, Anomaly] → Merge Report (IGroupData) → Enum Selector → [Report High/Low/Zero]`），并在 `ConfigureRun` 中配置**全部七项**宿主能力。每个完整平台 demo 都把 Run / Resume / Stop / Pause /「从检查点继续」绑定到它。
    注意：`* Trimmed` 兄弟 demo 是**纯节点编辑器** —— 它们既不引用 `Common/Lib`，也不引用编译器/运行时。它们是*编辑器*面的裁剪安全权威 demo，不是本特性编译执行层的。

## 2. 运行声明

- ✅ **确实于 2026-10-01 构建并运行。** 命令：在控制台工程（`net10.0`，启用 `Nullable` 与 `ImplicitUsings`）中 `dotnet build -c Debug`，随后 `dotnet run -c Debug`；该工程以工程引用方式引用 `Src/Core/VeloxDev.Core`、`Src/Core/VeloxDev.Core.Extension` 与 `Src/Generators/VeloxDev.Core.Generator`（最后一个作为 analyzer，`ReferenceOutputAssembly=false`），运行于 .NET SDK 10.0.401。程序即 `07_完整代码` 全文打印的版本，加上其中列出的组件文件。

  记录输出：

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
[7] checkpoint: attempt=1 outputs=1 shape=<three RuntimeId GUIDs>
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

  每一行都与所属步骤声明的**预期结果**一致。有三行值得再读一遍：

  - `[8] … attempt=1` —— 重试**不是**对图的一趟新遍历，所以输出注册表的重叠戳不动，join 聚合保持正确。
  - `[7] … refused … status=Idle` —— 恢复在**触碰会话之前**被拒绝，这就是 `Status` 仍读作 `Idle`、而不是谎称发生过一次运行的原因。
  - `[11] … overlap=True` / `overlap=False` —— 扇出默认确实并发，上限为 1 时确实串行。

- ✅ **另由随附测试套件验证**（阅读，未重新执行）：上文第 1 节点名的每一条契约都由测试钉住，包括 `MaxParallelBranches` 上限与 `MaxRetainedLogs` 行为 —— 这两项没有 demo 演练。
- ⚠️ **未通过运行 GUI 宿主验证。** 各平台 demo（`Examples/Workflow/WPF/Demo`、`Avalonia/Demo`、`Blazor/Demo`、`MAUI/Demo`、`WinUI/Demo`、`WinForms/Demo`、`Jalium/Demo`）**未**构建或启动 —— 它们是 GUI 宿主（WPF 为 `net9.0-windows`，Avalonia 为 `net8.0`，外加 MAUI/WinUI/Blazor 工作负载），本页关于它们的说法读自源码，而非运行中的应用。把「真实仓库中的位置」当作源码验证，而非运行验证。
- ⚠️ **一条无法钉死的说法。** 已验证的构建把快速开始的组件拆在多个文件里（demo 仓库也如此）。一次把两个生成组件放在**同一**文件里的探针也能编译，因此「一个组件一个文件」是 demo 的约定而非生成器的硬性要求；把整个程序放进单文件的形式未重新验证。连接预览的 GUI 绘制（各 demo 的曲线视图）同样只做了源码验证。
