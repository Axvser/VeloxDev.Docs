# 工作流系统 — 终端结果编译

很多时候你并不想“从头跑整张图”，只想**算某个节点的结果**：例如只想知道 `Report` 会输出什么，而不需要动 `Discard` 这条旁支。这正是 `CompileRole.Terminal` 的用途——**无需显式起点**。

本页代码沿用前几页的 `tree / source / report / discard` 与同一个 `compiler` 实例。

```csharp
var terminalGraphs = await compiler.CompileAsync(report, CompileRole.Terminal);
var terminalGraph = terminalGraphs[0];
Console.WriteLine($"Terminal entries={terminalGraph.Entries.Count} " +
                  $"first={terminalGraph.Entries[0].GetType().Name}");

var terminalCtx = new RuntimeContext { Data = 2.0, Target = report };
await new RuntimeEngine().RunAsync(terminalGraph, terminalCtx, CancellationToken.None);
Console.WriteLine($"Terminal status={terminalCtx.Status} targetReached={terminalCtx.TargetReached} " +
                  $"data={terminalCtx.Data}");
```

## 1. 反向锥编译做什么

`CompileAsync(node, CompileRole.Terminal)` 的实现（`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs`）：

1. **沿 `Sources`（入线）反向 BFS** 收集目标的“祖先锥”：所有能经**有效边**（`AccessAsync` 接受）到达该目标的节点。无效边按“未连接”处理，不进锥。
2. **自动推导锥的入口前沿**：锥内没有 in-cone 前驱的节点就是入口（控制器 / 数据源 / 无输入节点），不需要你指定起点。
3. **沿锥做一次受限正向编译**：入口唯一 → 直接正向编译；入口多个（独立生产者汇入同一漏斗）→ 编译为扇出支 + 共同的汇合链。

示例里 `Report` 的锥 = `{Source, Report}`（`Discard` 不在其中），入口 = `Source`。所以产物只有一段 `ChainSegment[Source, Report]`，与上一页从 `Source` 正向编译不同——**没有 `ParallelSegment`，也没有 `Discard`**。

**预期结果：**

```text
Terminal entries=1 first=ChainSegment
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
Terminal status=Completed targetReached=True data=4
```

对比 [04 编译与正向运行](../04_compile-and-run/index.md) 的输出：**打印里少了 `[Discard]` 一行** —— 旁支既未被本次编译纳入，也未被驱动。

## 2. 目标追踪：Target / TargetReached

给会话设置 `Target = report`，引擎驱动到与 `Target` 引用相等的节点时置 `TargetReached = true`；`context.Data` 落在 `Report` 的输出 `4`。

- `TargetReached == false` 表示运行期“没到目标” —— 例如锥上某个 **Router** 在运行期选到了兄弟支，流程在该支结束，**目标不被驱动、也不编造任何结果**（与正向语义完全一致）。见测试 `CompileToReverseTests.RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`。
- 锥上的 Router 保留真实 `BranchSegment` 语义，只是**只编通往锥的支**（`RestrictRouteToCone`；若一个 Router 有多条支都通向目标，则无法用一次正向运行表达 → 抛 `InvalidOperationException` 而非瞎猜）。

**预期结果：** 上例 `targetReached=True`、`data=4`；若把 `Target` 换成一条不在锥内的节点，该节点不会出现在图里。

## 3. 与正向结果一致

同一目标，Terminal 编译运行结果与“从锥入口正向跑”结果一致（线性/扇入汇合都成立），因为两者都是同一份数据流语义。测试 `CompileToReverseTests.LinearChain_TargetMidCone_CompilesFromOwnEntry_MatchesForwardRun` 专门断言这一点。

> 能力边界：当前反向编译要求锥是**串-并联**（独立生产者最终收敛到一个共同汇合点再通向目标）。两层及以上的独立漏斗当前无法表达，会抛带 `funnel` 的说明性异常 —— 见 `CompileToReverseTests.MultiLevelFanInAcrossIndependentEntries_ThrowsInformative`。

## 下一步

图画、编译、运行都已跑通，最后做 [06 序列化](../06_serialization/index.md) 持久化整棵树。
