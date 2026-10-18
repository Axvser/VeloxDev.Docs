# 工作流系统 — 快速开始

VeloxDev WorkflowSystem 是一套跨平台的可视化工作流编辑与执行引擎。你用四种组件 —— **Tree**、**Node**、**Slot**、**Link** —— 搭建一张图：给 partial ViewModel 标上 `[WorkflowBuilder.*]` 特性，Roslyn 源生成器会补出完整的 ViewModel（属性、命令、Helper 接线、撤销/重做、连接管线）。引擎核心与 UI 框架无关；各平台的 *适配器* 提供渲染行为，属于独立的 `08_platform-adapters` 特性。

引擎有三种执行方式：

1. **节点级** —— 驱动单个节点的 `ReceiveCommand`，它把 `TaskContext` 转交给 `Helper.ReceiveAsync`。
2. **边级** —— 节点沿连线广播负载（`StandardBroadcastAsync`），每条通过校验的边把 `TaskContext` 投递给下游节点。
3. **链级（编译执行）** —— `CompilerViewModel.CompileAsync(node, role)` 把可达子图分解成一张无环的 `CompiledGraph`，再由 `RuntimeEngine.RunAsync(graph, RuntimeContext)` 驱动。角色决定编译器如何理解这个节点：`CompileRole.Root`（该节点发起一次正向运行）或 `CompileRole.Terminal`（该节点是想要的结果 —— 编译器反向编译它的祖先锥）。

编译执行之外还有一层可选的**宿主能力层**：暂停闸门、观察者、重试策略、错误接收器、补偿器、检查点存储与日志写入器。它们都不是必需的 —— 全部不设置时，运行行为与这层出现之前完全一致 —— 本快速开始会逐一走一遍。

本特性的页面假定你使用[安装与创建项目](01_安装与创建项目/index.md)里创建的 `.NET`/C# 控制台工程。不需要 GUI：编译与运行都在核心引擎里无头完成。

## 快速开始 — 子页面

| 页面 | 你要做的事 |
|---|---|
| [前置条件](00_前置条件/index.md) | 支持的目标框架、SDK、仓库结构 |
| [安装与创建项目](01_安装与创建项目/index.md) | 创建控制台工程并引用 `VeloxDev.Core`（以及 `VeloxDev.Core.Extension`） |
| [定义组件](02_定义组件/index.md) | 声明 Tree / Slot / Link / Node 类与它们的 `NodeHelper<T>` 执行逻辑 |
| [构建图](03_构建图/index.md) | 实例化画布、注册节点、设置槽通道、建立连接 |
| [编译并运行（Root）](04_编译并运行/index.md) | 用 `CompileRole.Root` 正向编译，并用 `RuntimeEngine` 运行 |
| [编译结果（Terminal）](05_终端编译/index.md) | 用 `CompileRole.Terminal` 反向编译结果（`Target` / `TargetReached`） |
| [序列化与重建树](06_序列化/index.md) | 把整棵树序列化为 JSON 并重建 |
| [完整代码](07_完整代码/index.md) | 完整核心程序：每个文件，全文 |
| [暂停与恢复运行](08_暂停与恢复/index.md) | 用 `ManualExecutionGate` 在节点边界停住运行 |
| [观察运行并读取结果](09_观察与报告/index.md) | 用 `IExecutionObserver` 看时间线；读取 `RunOutcome` |
| [重试失败节点并补偿坏运行](10_重试与补偿/index.md) | 重试抛异常的节点；把坏运行已完成的节点交还宿主 |
| [检查点与日志文件](11_检查点与日志/index.md) | 记下运行位置、从该处恢复、改道并限制日志 |
| [并行扇出、并发上限与编译大纲](12_并行与大纲/index.md) | 扇出并发、它的上限，以及 `CompiledOutline` |
| [验证与运行声明](13_验证与运行声明/index.md) | 对照测试与 demo 的验证，以及如实的运行声明 |

每个页面都为编号步骤给出可观察的**预期结果**；从[完整代码](07_完整代码/index.md)起的页面由作者实际构建并运行过的输出支撑 —— 记录的运行见[验证与运行声明](13_验证与运行声明/index.md)。
