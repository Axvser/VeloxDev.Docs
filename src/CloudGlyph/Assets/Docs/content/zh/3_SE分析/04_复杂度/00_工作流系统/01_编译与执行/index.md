# 工作流系统 — 编译与执行的复杂度

渐近界使用 KaTeX；每个数字都落在所引源码上。全部位于 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/`。

## 编译（`CompilerViewModel.CompileAsync`）

编译是一次有记忆的分解。设 $V$ 个节点、$E$ 条边（连接）：

$$
T_{\text{compile}} = O(V + E)
$$

- **Root**（`CompileGraphAsync`）：从控制器向下游走。`CompileState.Visited` 保证每个节点只处理一次；每个节点枚举其输出槽的 `Targets`，每条边运行发送端 `AccessAsync` 静态闸门（`GetValidTargetsAsync`）—— 被拒边被丢弃，所以无效边各只花一次 `AccessAsync`。线性段折成 `ChainSegment`；路由器递归展开每个路由键（`BranchSegment`，每个选项是一个子 `CompiledGraph`）；普通节点扇出与多键扇出成为 `ParallelSegment`，其分支各是一张子图。Order 是单调连续的计数器（`Offset` 被带入下游图，不重置为零），join 登记每个 join 点 $O(\text{inputs})$。静态剪枝（`MarkStoppedBranch`）对跳过的分支拓扑只走一遍来盖 `Order = -1`；同样受 `Visited` 守卫。
- **Terminal**（`CompilerViewModel.Reverse.cs`）：`BuildAncestorConeAsync` 沿 `Sources` 做反向 BFS，使用同样的逐边 `AccessAsync` 闸门 —— 在锥上是 $O(V + E)$。`CompileConeAsync` 推导入口前沿，然后委托给限制在锥内的同一正向遍历；路由器保持真实 `BranchSegment` 语义，只编译锥内分支（`RestrictRouteToCone`）。

空间是 $O(V + E)$：分段树、visited 集合与锥。

## 编译图大纲（`CompiledOutline.Of`）

一趟深度优先遍历，每个分段一行，链的标签由节点类型名连接而成：

$$
T_{\text{outline}} = O(V + E_s), \qquad S_{\text{outline}} = O(E_s)
$$

$E_s$ = 分段数。它**只计算一次** —— 编译图在编译后冻结，不需要让扁平视图与之保持同步。一条 $N$ 节点链的标签连接是 $O(N)$ 字符串拼接，所以总量仍是 $O(V)$。

## 顺序执行（`RuntimeEngine.RunAsync`）

`RunAsync` 一趟一趟地遍历图的分段；每个分段的代价是其被驱动节点之和：

| 分段 | 代价 |
|---|---|
| `ChainSegment` | $O(N_{\text{chain}})$ —— 对线性分段走一趟，逐个 await `ReceiveAsync` 并写 `context.Data` |
| `BranchSegment` | $O(N_{\text{branch}})$ —— 静态分支用编译期锁定的 `CompileKey` 在 $O(1)$ 内选定（选项扫描）；动态分支多付一次 `ResolveRouteKey` 加对 `Options` 的线性扫描 |
| `ParallelSegment` | $\sum_{\text{branches}} O(N_{\text{branch}})$ —— 分支**并发启动**，但墙钟收益只对 I/O 型分支真实，因为它们共享一个线程 |

每次 `DriveAsync` 是 $O(1)$ 簿记加上节点自身工作：向 `IRuntimeAware` 节点注入会话、设置 `CurrentOrder`；当节点是多输入 join 点时，调用 `CollectGroupedInputs` 把分组输入装箱为 `IGroupData` —— 对已注册输入源的字典构建，$O(\text{inputs})$，预分配尺寸以避免扩容。

对整张图、$N$ 个被驱动节点：

$$
T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)
$$

以节点数计（墙钟时间由节点工作负载主导，例如 demo 中的 `Task.Delay`）。

### 带回并发上限的扇出

有 $B$ 个分支、上限 $c$ 的 `ParallelSegment` 分 $\lceil B/c \rceil$ 波运行；信号量每分支 $O(1)$（一对 `WaitAsync` / `Release`）：

$$
T_{\text{fan-out}} = \frac{1}{c}\sum_{j=1}^{B} T_{\text{branch}}(j) \quad (\text{bounded by } \lceil B/c \rceil \text{ waves}), \qquad S_{\text{fan-out}} = O(B)
$$

`c = null` 意味着 $c = B$（完全重叠）；`c = 1` 退化为顺序代价。空间是每分支一个 `BranchRuntimeContext` 数组加每分支一个 `Task<bool>` —— 注意**所有 $B$ 个任务一开始就创建**（`new Task<bool>[count]`），所以上限约束的是并发*工作*，而非已启动任务数。

### 重定向

重定向朝目标 Order 重跑整张图，跳过契约保留前缀（`Order < target`）；最多 50 次（`MaxRedirects`）：

$$
T_{\text{redirect}} = O(50 \cdot N)
$$

每一趟还会重走分段列表，所以常数里包含分段数。

## 检查点

| 操作 | 时间 | 空间 |
|---|---|---|
| `ExecutionCheckpoint.NodesOf(graph)`（每次运行一次） | $O(V)$ | $O(V)$ |
| `RuntimeContext.Snapshot()`（每次成功后；internal） | $O(R)$ —— $R$ = 已注册输出，≤ $V$ | $O(R)$ |
| `InMemoryCheckpointStore.SaveAsync` | $O(1)$（锁下一次引用交换） | 保留 $O(R)$ |
| `FileCheckpointStore.SaveAsync` | $O(R)$ —— JSON 写入，信号量后串行 | $O(R)$ |
| `RequireSameShape`（每次恢复一次） | $O(\min(V, |\text{Shape}|))$ | $O(1)$ |
| `Restore`（每次恢复一次） | $O(V)$ | $O(V)$ |
| `ExecutionCheckpoint.Rekey`（宿主调用） | $O(V + R)$ | $O(V + R)$ |

快照代价正是检查点在**每个节点之后**写、而不是每趟之后写的原因：每节点 $O(R)$，对比整体重算的 $O(V) \cdot$ 节点数。

负载很大时 `Snapshot()` 并不便宜：它存下每个已完成输出；对 join 还会把 `IGroupData` 改写成普通字典，每个组负载 $O(\text{inputs})$。

## 宿主能力开销

每个接缝都是一次 `null` 检查，配置后加一次调用。设 $N$ 个被驱动节点：

| 接缝 | 配置后每节点代价 |
|---|---|
| `IExecutionGate` | $O(1)$ —— 开闸时一次 `IsCompleted` 检查（无分配、不写 `Status`）；仅在关闭时等待 `TaskCompletionSource` |
| `IExecutionObserver` | 每个成功节点 2 次调用（`NodeStarted`、`NodeSucceeded`）+ 每分支 1 次 + 每次运行 2 次 |
| `INodeRetryPolicy` | **每次抛出的异常** 1 次调用，外加一次 `Task.Delay` |
| `IExecutionErrorSink` | 每次失败 1 次调用；节点抛异常时 2 次（节点自己的记录，然后引擎的决定） |
| `IExecutionCheckpointStore` | 每个成功节点 1 次快照 + 1 次保存 |
| `IExecutionCompensation` | 每个成功驱动节点 1 次调用，但**仅当**结果为 `Failed` 或 `Cancelled` —— 完成的运行是 0 次 |
| `ILogWriter` | 每行 $O(1)$，位于 `AppendLog` 内 —— 计入节点自身工作 |

全部不设置时，新增总代价是 $N$ 次 `null` 检查：运行与这层出现之前完全一致，这正是声明的契约。

### 有界与无界日志

默认 `Logs` 每行增长 $O(1)$。设置 `MaxRetainedLogs = m` 后，`AppendLog` 内的保留裁剪是：

$$
T_{\text{trim}} = O(1) \text{ amortized per line}, \qquad S_{\text{Logs}} = O(m)
$$

因为每次调用最多加一行，所以至多需要一次 `RemoveAt(0)` —— `while` 循环只跑一次。`SnapshotLogs()` 是 $O(|\text{Logs}|)$ 加一次数组分配，是跨线程读取 `Logs` 唯一被认可的方式。

## 内存占用汇总

| 结构 | 空间 | 依据 |
|---|---|---|
| `CompiledGraph` + 分段 | $O(V + E)$ | 分段树 + visited 集合 + 锥 |
| `CompiledOutline` 行 | $O(E_s)$ | 每分段一行 |
| 运行时输出注册表 | $O(\text{driven nodes})$ | 带趟戳的 `RegisterOutput` 表 |
| 本次运行完成列表（用于补偿） | $O(\text{successes})$ | 每节点一条；重驱动时移动而非重复 |
| 扇出分支上下文 | $O(B)$ | 每分支一个 `BranchRuntimeContext` + 一个任务 |
| `ExecutionCheckpoint` | $O(V + R)$ | shape + types + outputs |
| `Logs` | $O(\text{lines})$，或上限 $O(m)$ | `ObservableCollection<string>` + 可选裁剪 |
| 序列化图快照 | $O(P_{\text{graph}})$ | writer 在图边界停止 |

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| 编译（`CompilerViewModel`，Root / Terminal） | $O(V+E)$ | $O(V+E)$ | 有记忆的分解 + 反向锥 + visited 集合 |
| `CompiledOutline.Of` | $O(V + E_s)$ | $O(E_s)$ | 一趟 DFS，只算一次 |
| 驱动分段（`RuntimeEngine`） | $O(N)$ | $O(N)$ | 对分段走一趟；join 聚合 $O(\text{inputs})$ |
| 扇出，上限 $c$、$B$ 个分支 | $\lceil B/c \rceil$ 波 | $O(B)$ | 每组一个信号量，所有任务预先启动 |
| 重定向最坏情况 | $O(50 \cdot N)$ | $O(N)$ | `MaxRedirects = 50` |
| 快照 + 保存检查点 | $O(R)$ | $O(R)$ | 每个成功节点 |
| 恢复（`RequireSameShape` + `Restore`） | $O(V)$ | $O(V)$ | shape 比较 + 输出重注册 |
| 宿主能力，全部不设置 | $O(N)$ 次 `null` 检查 | $O(1)$ | 精确的 2026-09-27 之前行为 |
