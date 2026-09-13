# 工作流系统 — 编译与正向运行

本页代码沿用 [03 构建画布](../03_构建画布/index.md) 构建好的 `tree / source / report / discard`（类型见 [02 定义组件](../02_定义组件/index.md)；最终单一文件见 [07 完整代码](../07_完整代码/index.md)）。

## 1. 编译（CompileRole.Root）

编译器只有一个统一入口：

```csharp
var compiler = new CompilerViewModel();
var forwardGraphs = await compiler.CompileAsync(source, CompileRole.Root);
var forwardGraph = forwardGraphs[0];
Console.WriteLine($"Forward entries={forwardGraph.Entries.Count} " +
                  $"first={forwardGraph.Entries[0].GetType().Name} " +
                  $"second={forwardGraph.Entries[1].GetType().Name}");
```

- `CompileRole.Root`：把 `source` 当作**根节点**，沿 `Targets`（出线）向下游编出它可达的整个子图。
- `CompileRole.Terminal`：把节点当作**结果终端**，见 [05 终端结果编译](../05_终端编译/index.md)。
- `CompileAsync(node, role, ct)` 返回 `IReadOnlyList<CompiledGraph>`（多图语义；本实现两种角色都产出一张图），同时写入 `Compiler.Graphs`。

**预期结果：**

```text
Forward entries=2 first=ChainSegment second=ParallelSegment
```

## 2. 段模型（CompiledGraph.Entries）

`CompiledGraph` 是一组有序的 `CompileSegment`（`CompileSegment` 派生类，各有 `Id` / `Depth`）。分解规则在 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs`：

| 拓扑 | 产物段 | 说明 |
|---|---|---|
| 线性链（单入单出） | `ChainSegment` | `Nodes`：顺序执行的节点列表 |
| 节点实现 `ICompileTimeRouter` | `BranchSegment` | `Router` + `Options`（`BranchOption`：`Key/Label/Graph/IsTerminal`） |
| 一个出口扇向多个下游 | `ParallelSegment` | `Branches`：各支子图 |

三种段是全部 `CompileSegment` 具体类型（基类带 `Id` / `Depth`）。扇出既可能来自 Router 的某条路由键，也可能来自**普通节点的多条出线**——两者都会生成 `ParallelSegment`；各支子图由引擎**逐支顺序执行**（当前实现无真并发，共享会话非线程安全），并**在每支驱动前恢复扇出源负载**（上一支的输出不得泄漏给下一支）。多支出口若存在共同下游（汇合点），该点不单独成段，而是作为父图下一段 `ChainSegment` 的起点，编译时为其登记 `InputNodes`，运行期据此把各上游产物聚合为 `IGroupData` 注入 `Data`。

示例里 `Source` 是**普通节点**但出线扇向 `Report` 与 `Discard`，所以编译为：

```text
[ChainSegment(Source), ParallelSegment(Branches = [Chain(Report), Chain(Discard)])]
```

**路由节点**（实现 `ICompileTimeRouter` 的节点，如 Demo 的 `EnumSelectorNodeViewModel`）会按 `RouterCompileMode` 决定编译产物：

- `RouterCompileMode.Static`：编译期锁定当前选中分支，未选中分支被剪除（其下游收到 `Order = -1` 的绝对停止信号）。
- `RouterCompileMode.Dynamic`：编译期保留全部分支；运行期由 `ResolveRouteKey(ctx)` 按数据负载重新选键。

编译完成会给每个实现 `ICompileTimeAware` 的节点注入 `CompileContext`（全局序号 `Order`、链内 `ChainIndex`、子图偏移 `Offset`）。图本身**无环**。

**预期结果：** `source.CompileContext?.Order == 0`、`report.Order == 1`、`discard.Order == 2`（运行时打印见下）。

## 3. 运行（RuntimeEngine）

```csharp
var forwardCtx = new RuntimeContext { Data = 2.0 };
await new RuntimeEngine().RunAsync(forwardGraph, forwardCtx, CancellationToken.None);
Console.WriteLine($"Forward status={forwardCtx.Status} data={forwardCtx.Data} " +
                  $"sourceOrder={source.CompileContext?.Order} reportOrder={report.CompileContext?.Order} " +
                  $"discardOrder={discard.CompileContext?.Order}");
```

- `RuntimeContext` 实现 `IRuntimeContext`，即“编译器运行时会话”：UID / 日志 / 共享变量 / 执行位置。
- 引擎**按编译图驱动**：`ChainSegment` 逐个驱动节点，`BranchSegment` 先驱动 Router 再按其运行期键走选中支，`ParallelSegment` 逐支顺序执行并**恢复扇出源负载**（每支都读到同一份上游输出，而不是上一支的输出）。
- 驱动方式统一是 `node.GetHelper().ReceiveAsync(ctx, ct)`，返回值写回 `context.Data` 作为下游入参。节点实现 `IRuntimeAware` 会在驱动前收到同一个会话对象。

**预期结果（真实运行输出）：**

```text
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
  [Discard] kind=pass order=2 result=4
Forward status=Completed data=4 sourceOrder=0 reportOrder=1 discardOrder=2
```

解读：初始 `Data = 2.0` → `Source`（倍乘）产出 `4`；`ParallelSegment` 让 `Report` 与 `Discard` 各读到 `4`；最后 `context.Data` 为末支 `Discard` 的输出 `4`。`Status == "Completed"`；若中途取消则 `Status == "Stopped"`。

## 4. 四种执行入口

上下文体系：`IContext`（根，携带 `Data`）→ `IAccessContext`（增加 `IsCompilePhase` / `Sender` / `Receiver`）→ `ITaskContext`（节点 `ReceiveCommand → Helper.ReceiveAsync` 的入参契约）。编译侧 `ICompileContext` 与运行侧 `IRuntimeContext` 都派生自该体系。

| 入口 | API | 何时用 |
|---|---|---|
| 节点级 | `node.ReceiveCommand.Execute(new TaskContext(data, sender, receiver))` | 手动唤醒单个节点（无编译）；`TaskContext` 是 `ITaskContext` 的只读结构体载体 |
| 边级广播 | `helper.BroadcastAsync(payload, ct)` / `ReverseBroadcastAsync` | 沿具体连线做逐边投递（带 `Sender`/`Receiver`，`AccessAsync` 拒绝的边按“未连接”跳过） |
| 链级（正向） | `RuntimeEngine.RunAsync(graph, context)`（`CompileRole.Root` 产物） | 从控制器/起点向下游跑整条编译图 |
| 终端结果运行 | `RuntimeEngine.RunAsync(graph, context)`（`CompileRole.Terminal` 产物）+ `context.Target` | 只算某个节点的值（见下一页） |

引擎自身驱动不会触发 `ReceiveCommand` / `BroadcastCommand` —— 下游派发由引擎独占。多输入汇合点运行时收到的是 `IGroupData`（`context.Data is IGroupData g`，以“来源节点 → 该节点输出”的只读字典读取各上游）；`IRedirectable` 节点出错（`Error`/`Warn`/异常）时可回到更早的编译状态重跑。

## 下一步

只算“一个节点的结果”而不需要起点节点？进入 [05 终端结果编译](../05_终端编译/index.md)。
