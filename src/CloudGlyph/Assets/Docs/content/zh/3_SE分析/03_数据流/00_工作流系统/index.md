# 数据流 — 工作流系统

PlantUML 时序图追踪工作流系统的核心数据流。参与者先声明后使用，`activate`/`deactivate` 成对，`alt/else/end` 平衡。

## 子页面

| 页面 | 流程 |
|---|---|
| [连接构建](00_连接构建/index.md) | 建立一条连接：`SendConnection` → `SetPreviewReceiver` → `ReceiveConnection` → `CreateLink` |
| [编译并运行（Root）](01_编译与运行/index.md) | 编译图（`CompileRole.Root`）并用 `RuntimeEngine.RunAsync` 驱动 |
| [反向 / 终端锥流程](02_终端锥/index.md) | 反向编译结果（`CompileRole.Terminal`）并跟踪 `Target` / `TargetReached` |
| [重定向重跑](03_重定向/index.md) | 节点内 `Error()` → `IRedirectable` → 整图重跑 |
| [并行扇出与并发上限](04_并行与上限/index.md) | 并发运行的扇出组，以及 `MaxParallelBranches` 将其串行化 |
| [从检查点恢复](05_从检查点恢复/index.md) | 每次成功后写检查点，再从它恢复（并让外来检查点被拒绝） |
| [广播派发（非 Compiler）](06_广播/index.md) | 边级广播派发（`StandardBroadcastAsync`）—— 非 Compiler 路径 |
| [一次驱动周围的宿主能力](07_宿主能力/index.md) | 包在单次节点驱动周围的能力：闸门、观察者、重试、错误接收器、补偿 |

## 各流程在哪里汇合

上述每条路径都终止于同一个方法 —— `IWorkflowNodeViewModelHelper.ReceiveAsync(ITaskContext, CancellationToken)` —— 节点只通过收到的**上下文类型**区分它们。Compiler 路径传入运行的 `IRuntimeContext`；广播路径每条边传入全新的 `TaskContext`。逐参数对照见 API 维度的 `04_执行机制` 页。

所有图共享两条不变量：

- **编译运行期间下游派发归引擎所有。** 节点通过 Helper 直接驱动；它们的 `ReceiveCommand` / `BroadcastCommand` 从不触发（`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`）。
- **编译运行时唯一有意义的成员是 `context.Data`。** `Sender` 与 `Receiver` 在那里恒为 `null`，因为引擎驱动的是图而非其边。
