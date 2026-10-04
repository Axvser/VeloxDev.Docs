# 工作流系统 — 快速开始

VeloxDev WorkflowSystem 是一个跨平台的可视化工作流编辑与执行引擎。你用四类组件 —— **Tree（画布）**、**Node（节点）**、**Slot（槽位）**、**Link（连线）** —— 来搭一张图：给 `partial` 的 ViewModel 打上 `[WorkflowBuilder.*]` 特性，Roslyn 源生成器就会补出完整的 ViewModel（属性、命令、Helper 接线、撤销/重做、连线管道）。引擎核心与 UI 框架无关；各平台的**适配器**提供渲染行为，属于另一个特性 `08_平台适配器`。

引擎有三种执行图的方式：

1. **节点级** —— 驱动单个节点的 `ReceiveCommand`，它把 `TaskContext` 转交给 `Helper.ReceiveAsync`。
2. **边级** —— 节点沿自身连线广播载荷（`StandardBroadcastAsync`）；每条被接受的边把一个 `TaskContext` 投递给下游节点。
3. **链级（编译式）** —— `CompilerViewModel.CompileAsync(node, role)` 把可达子图分解为一张无环的 `CompiledGraph`，再由 `RuntimeEngine.RunAsync(graph, RuntimeContext)` 驱动。role 告诉编译器*这个节点意味着什么*：`CompileRole.Root`（该节点发起一次正向运行）或 `CompileRole.Terminal`（该节点就是你要的结果 —— 编译器反向编译它的祖先锥）。

在编译运行之外还有一层**可选的宿主能力层**（2026-09-27 加入）：暂停门、观察者、重试策略、错误接收器、补偿器、检查点存储与日志写入器。没有一项是必需的 —— 全部不设置时，运行的表现与它们存在之前一模一样 —— 本快速开始会把它们逐一走一遍。

本特性的页面都以 [安装 / 添加依赖](01_安装/index.md) 里创建的 `.NET`/C# 控制台项目为前提。不需要 GUI：编译与运行都在核心引擎里无头完成。

## 快速开始 — 子页

| 页面 | 你会做什么 |
|---|---|
| [前置条件](00_前置条件/index.md) | 受支持的目标框架、SDK、仓库结构 |
| [安装 / 添加依赖](01_安装/index.md) | 建控制台项目并加上 `VeloxDev.Core`（序列化那步再加 `VeloxDev.Core.Extension`）引用 |
| [定义组件](02_定义组件/index.md) | 声明 Tree / Slot / Link / Node 类及其 `NodeHelper<T>` 执行逻辑 |
| [构建画布](03_构建画布/index.md) | 实例化画布、登记节点、设置槽位通道、连起来 |
| [编译与正向运行](04_编译与运行/index.md) | 用 `CompileRole.Root` 正向编译，用 `RuntimeEngine` 运行 |
| [终端结果编译](05_终端编译/index.md) | 用 `CompileRole.Terminal` 反向编译某个结果（`Target` / `TargetReached`） |
| [序列化](06_序列化/index.md) | 把整棵树序列化成 JSON 并重建 |
| [完整代码](07_完整代码/index.md) | 核心流程的完整程序：每个文件都全文给出 |
| [暂停并恢复一次运行](08_暂停与恢复/index.md) | 用 `ManualExecutionGate` 把运行握在节点边界 |
| [观察一次运行并读取它的结局](09_观察与报告/index.md) | 用 `IExecutionObserver` 看时间线；读 `RunOutcome` |
| [重试失败的节点与补偿一次糟糕的运行](10_重试与补偿/index.md) | 重试抛异常的节点；把失败运行的成果交还宿主 |
| [检查点与日志文件](11_检查点与日志/index.md) | 写下运行位置、从它恢复、把日志导到文件并限制内存保留 |
| [并行扇出、它的并发上限与编译大纲](12_并行与大纲/index.md) | 扇出并发、它的上限，以及 `CompiledOutline` |
| [验证与运行声明](13_验证与运行声明/index.md) | 对照测试与 demo 的验证，以及诚实的运行声明 |

每一页的每个编号步骤都给出可观察的 **预期结果**；从 [完整代码](07_完整代码/index.md) 起，页面上的输出都由作者真正构建并运行得到 —— 完整运行记录见 [验证与运行声明](13_验证与运行声明/index.md)。
