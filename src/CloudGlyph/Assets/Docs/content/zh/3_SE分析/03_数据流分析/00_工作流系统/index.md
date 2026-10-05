# 数据流分析 — 工作流系统

用 PlantUML 时序图追踪工作流系统的核心数据流。图中参与者先声明后使用，`activate`/`deactivate` 成对，`alt/else/end` 块平衡。

## 子页

| 页面 | 流程 |
|---|---|
| [连接流程](00_连接/index.md) | 建立一条连线：`SendConnection` → `ReceiveConnection` → `CreateLink` |
| [编译与运行（Root）](01_编译与运行/index.md) | 编译一张图（`CompileRole.Root`）并用 `RuntimeEngine.RunAsync` 驱动 |
| [反向 / 终端锥流程](02_终端锥/index.md) | 反向编译某个结果（`CompileRole.Terminal`）并追踪 `Target` / `TargetReached` |
| [重定向重跑](03_重定向/index.md) | 节点内 `Error()` → `IRedirectable` → 整图重跑 |
| [并行扇出与并发上限](04_并行与上限/index.md) | 扇出组并发运行，以及 `MaxParallelBranches` 把它串行化 |
| [从检查点恢复](05_检查点恢复/index.md) | 每个节点成功后写下检查点，再从它恢复（以及外来检查点被拒绝） |
| [广播派发（非 Compiler）](06_广播/index.md) | 边级广播派发（`StandardBroadcastAsync`）—— 非 Compiler 路径 |
| [包在一次驱动周围的宿主能力](07_宿主能力/index.md) | 包在一次节点驱动周围的各项能力：门、观察者、重试、错误接收器、补偿 |

## 各条流程在哪里汇合

上面每条路径最终都落在同一个方法 —— `IWorkflowNodeViewModelHelper.ReceiveAsync(ITaskContext, CancellationToken)` —— 节点只靠收到的**上下文类型**区分它们。Compiler 路径传的是运行的 `IRuntimeContext`；广播路径每条边传一个新的 `TaskContext`。逐参数的对照见 API 维度的 `04_执行机制` 页。

所有图都成立的两条不变量：

- **编译运行期间由引擎独占下游派发。** 节点直接经它的 Helper 被驱动，其 `ReceiveCommand` / `BroadcastCommand` 从不被触发（`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`）。
- **编译运行下 `context.Data` 是唯一有意义的成员。** 那里 `Sender` 与 `Receiver` 恒为 `null`，因为引擎驱动的是图而不是它的边。
