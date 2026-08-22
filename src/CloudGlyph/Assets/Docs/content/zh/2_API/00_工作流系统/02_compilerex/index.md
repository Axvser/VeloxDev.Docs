# Workflow System — 命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`

V7 编译流水线：编译期把从起点可达的子图分解成无环编译图（多图语义）；执行引擎在运行期驱动图。

> 想了解 Compiler 路径与非Compiler（无状态广播）路径的差异——入口、参数、时序——见 [执行机制](../05_执行机制)。

| 类型 | 签名 / 成员 |
|---|---|
| `CompilerViewModel` | `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CancellationToken ct = default)`（`T : IWorkflowViewModel`，起点必须是 `IWorkflowNodeViewModel`）；`ObservableCollection<CompiledGraph> Graphs`。分解：线性段 → `ExecuteEntry`；`ICompileTimeRouter` 节点 → `BranchEntry`（静态按当前 key 剪枝，动态全保留）；路由 key 指向多个下游 → `ParallelEntry`（扇出/汇聚）；无下游 → 终端分支（`IsTerminal`）；所有分支出口共同指向的节点为汇合点，作为父图下一段链的起点（序号带偏移，不归零）。编译完给每个 `ICompileTimeAware` 节点注入 `CompileContext`；线性链续接时逐条输出边经 `AccessAsync`（编译期，`IsCompilePhase = true`）做静态检测，非法边按未连接跳过。 |
| `CompiledGraph` | `ObservableCollection<ActionEntry> Entries` —— 一张编译图；可嵌套 |
| `ActionEntry` | 抽象基类（`Guid Id`、`int Depth`、`bool IsSkipped`）；具体：`ExecuteEntry`、`BranchEntry`、`ParallelEntry` |
| `ExecuteEntry` | `ObservableCollection<IWorkflowNodeViewModel> Nodes` —— 线性段 |
| `BranchEntry` | `IWorkflowNodeViewModel? Router`、`ObservableCollection<BranchOption> Options`、`bool IsDynamic`、`object? CompileKey`（编译期锁定的 key） |
| `BranchOption` | `object? Key`、`string? Label`、`CompiledGraph? Graph`、`bool IsSkipped`、`bool IsTerminal` |
| `ParallelEntry` | `ObservableCollection<CompiledGraph> Branches` —— 扇出组；各分支顺序执行（顺序即「等待所有上游」的汇聚语义） |
| `CompilerEngine` | `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct)` —— 驱动一张图的所有条目；重定向时带目标 Order 重跑整张图 |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()`、`Task<object?> ResolveRouteKey(object? payload)` |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` —— 返回要回退的编译状态 Order |
| `ICompileTimeAware` | `void AttachCompileTimeContext(ICompileContext context)`、`ICompileContext? CompileContext` |
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)` |
| `ICompileContext : IAccessContext` | 继承 `Data`/`IsCompilePhase`/`Sender`/`Receiver`；新增 `int Order`、`int ChainIndex`、`int Offset`（`Order = -1` = 绝对停止） |
| `IRuntimeContext : ITaskContext` | `Uid`、`Sequence`、`Logs`、`CurrentEntry`、`NodeIndex`、`BranchKey`、`Attempt`、`IsRunning`、`Status`、`CurrentOrder`、`RedirectRequested`、`EndedWithError`、`PendingRedirectTarget`；`new Data { get; set; }`（可写链式结果）；`Log()`、`Error()`、`Warn()`、`Set()`、`TryGet()` |
| `RuntimeContext` | `IRuntimeContext` 的默认实现（`[VeloxProperty]` 成员 + 共享变量字典；`IsCompilePhase = false`） |
| `CompileContext` | `ICompileContext` 的默认实现（`Order`、`ChainIndex`、`Offset`；`IsCompilePhase = true`、`Data = null`、`Sender`/`Receiver` 由编译器按边填入） |
| `RouterCompileMode` | `Static`（编译期锁定 key、静态剪枝）/ `Dynamic`（运行期重解析） |

执行语义（`CompilerEngine`）：`ExecuteEntry` 逐个驱动节点 —— 跨链回退时跳过 `Order < target` 的节点；节点在 `ReceiveAsync` 中调用 `RuntimeContext.Error()/Warn()` 或抛异常即请求重定向 —— 若实现 `IRedirectable`，引擎按返回的 Order **重跑整张图**（跳过目标之前的节点，可跨链；目标是 Router 时只重新路由、不重新计算），否则流程结束、状态 `-1`。`BranchEntry` 静态模式用锁定 `CompileKey`，动态模式经 `ResolveRouteKey` 重解析；选中终端分支（`IsTerminal`）即结束。`ParallelEntry` 顺序执行所有分支子图。回退超过 50 次（`MaxRedirects`）后放弃。

**示例** —— 从控制器节点使用 `CompileAsync` + `RunAsync`：`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`，第 29-58 行。

*源码：`WorkflowSystem/CompilerEx/CompilerViewModel.cs`、`CompilerEngine.cs`、`CompiledGraph.cs`、`CompileContext.cs`、`RuntimeContext.cs`、`IRedirectable.cs`、`ActionEntry/*.cs`、`Interfaces/*.cs`。*
