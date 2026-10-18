# 工作流系统 — 编译一个结果（Terminal）

有时你不想从控制器运行整张图 —— 你只想要**某个节点的值**（一份报告、一个计算结果、单个输出）。把该节点以 `CompileRole.Terminal` 传入：编译器沿 `Sources` 反向走有效边，收集它的*祖先锥*，自动推导锥的入口前沿，只编译产出该节点所需的部分。不需要显式起点 / 控制器。见 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs`。

## 1. 反向编译结果节点

以 `BiasNode`（链中间节点）为目标。它的锥是 `{ Ticker, Bias }`，编译图与从 `Ticker` 正向运行形状相同，但在 `Bias` 停止 —— `Printer` 在锥外，不参与编译：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

public static async Task<RuntimeContext> RunResultAsync(QuickTree tree)
{
    var bias = tree.Nodes.OfType<BiasNode>().Single();

    var compiler = new CompilerViewModel();
    var graphs = await compiler.CompileAsync(bias, CompileRole.Terminal, CancellationToken.None);
    var graph = graphs[0];

    var result = new RuntimeContext { Target = bias };
    await new RuntimeEngine().RunAsync(graph, result, CancellationToken.None);

    Console.WriteLine(result.TargetReached);   // True
    Console.WriteLine(result.Status);          // Completed
    Console.WriteLine(result.Data);            // tick->bias   (NOT tick->bias->print)
    return result;
}
```

**预期结果：** 运行在 `Bias` 之后停止；`result.Data` 是 `"tick->bias"`（结果节点自身的输出）；因为该节点确实被驱动过，`result.TargetReached == true`。在任何运行（Root 或 Terminal）上设置 `RuntimeContext.Target`，引擎就会跟踪该节点是否被驱动。

## 2. 锥上的正向一致语义

Terminal 编译**不会**压平或猜测分支。通往目标的路上，路由器保持真实的 `BranchSegment` 语义，但只编译目标落在锥内的分支。如果运行期路由器解析到*兄弟*分支（不通向目标），流程就在到达目标前结束 —— 与正向语义完全一致。目标绝不会被虚构：

- 选中的分支到达目标 → 目标运行，`RuntimeContext.TargetReached == true`。
- 路由器选择兄弟分支 → 目标未被驱动，`TargetReached == false`，也不会为它捏造值（`Data` 保持最后一个被驱动节点留下的内容）。
- 独立生产者不汇入同一个公共 join 的锥无法表达（编译器抛出信息明确的 `InvalidOperationException`，而不是猜测）。

这些规则由 `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/` 的 `CompileToReverseTests` 与 `RuntimeEngineRunTests` 钉住（例如 `RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`）。真实路由示例可读 `EnumSelectorNodeViewModel`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`），它的动态 `ResolveRouteKey` 根据数据负载选择分支。

**预期结果：** 对 demo 的 Enum Selector 目标做反向编译时，路由器保持存活，`BranchSegment.Options` 中只有锥内分支。

## 3. 上下文层级

流经节点的每个负载都建立在一个小层级上（都在 `VeloxDev.WorkflowSystem` / `VeloxDev.Core.WorkflowSystem.CompilerEx`）：

```text
IContext                 // object? Data  (real data at runtime, always null at compile time)
├── IAccessContext      // + IsCompilePhase, Sender, Receiver   (parameter of AccessAsync)
│   ├── ITaskContext    // ReceiveCommand → Helper.ReceiveAsync parameter (read-only)
│   └── ICompileContext // + Order / ChainIndex / Offset / InputNodes  (compile identity)
└── IRuntimeContext : ITaskContext
                        // runtime session: Uid / Logs / Status / Attempt / blackboard
                        // Set-TryGet / Target / TargetReached / writable Data
```

`RuntimeContext` 是你交给 `RuntimeEngine.RunAsync` 的具体会话。它是**共享的** —— 一次运行中注入每个节点 —— 每个成员对引擎的含义都不同：

| 成员 | 行为 |
|---|---|
| `Data` | 串起运行：引擎把每个节点的输出写回它，供下一个节点读取 |
| `Error()` | 请求一次**重定向** —— 节点未捕获的异常也一样。实现 `IRedirectable` 的节点可以回退到更早的编译状态（它的 `ICompileContext.Order`）；否则运行以 `Stopped`、`Order = -1` 结束 |
| `Warn()` | **不**重定向：它把报告级别设为 `Warning`，引擎带着节点返回的内容继续 |
| `Data is IGroupData` | 多输入 join 收到的是只读的*源节点 → 其输出*映射，而不是裸负载，于是可以通过 `group.TryGetValue(sourceNode, out var v)` 读取每个上游 |

编译图是无环的；重定向纯粹是运行期契约。

前往「序列化与重建树」。
