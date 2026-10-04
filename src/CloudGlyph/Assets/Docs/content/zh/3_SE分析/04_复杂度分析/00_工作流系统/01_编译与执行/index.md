# 工作流系统 — 编译与执行的复杂度

渐近界用 KaTeX 给出；每个数字都有源码出处。全部位于 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/`。

## 编译（`CompilerViewModel.CompileAsync`）

编译是一次带记忆的分解。设 $V$ 个节点、$E$ 条边（连线）：

$$
T_{\text{compile}} = O(V + E)
$$

- **Root**（`CompileGraphAsync`，第 59-249 行）：从控制器出发向下游走。`CompileState.Visited` 保证每个节点只被处理一次；每个节点枚举其输出槽位的 `Targets`，每条边跑一次发送方的 `AccessAsync` 静态门（`GetValidTargetsAsync` 第 414-447 行）—— 被拒绝的边被丢弃，所以非法边每条只花一次 `AccessAsync`。线性串折成 `ChainSegment`；路由按每个路由键递归展开（`BranchSegment`，每个选项一个子 `CompiledGraph`）；普通节点扇出与多键扇出成为 `ParallelSegment`，每条分支是一张子图。序号是单调连续的计数器（`Offset` 会带进下游图，而不是重置为零），汇合登记是每个汇合点 $O(\text{输入数})$。静态剪枝（`MarkStoppedBranch` 第 281-295 行）对一条被跳过的分支的拓扑走一遍、盖上 `Order = -1`；它同样有 `Visited` 守卫。
- **Terminal**（`CompilerViewModel.Reverse.cs`）：`BuildAncestorConeAsync`（第 33-74 行）是沿 `Sources` 的反向 BFS，配同一套逐边 `AccessAsync` 门 —— 对锥是 $O(V + E)$。`CompileConeAsync`（第 82-134 行）推导入口前沿，然后交给同一条受限的正向遍历；路由保留真实的 `BranchSegment` 语义，只编译在锥内的那条分支（`RestrictRouteToCone` 第 303-325 行）。

空间是分段树 $O(V + E)$，加上 visited 集合与锥。

## 编译大纲（`CompiledOutline.Of`）

一次深度优先遍历，每个分段一行，链的标签由节点类型名连接而成：

$$
T_{\text{outline}} = O(V + E_s), \qquad S_{\text{outline}} = O(E_s)
$$

$E_s$ = 分段数。它**只算一次** —— 编译后的图是冻的，所以没有任何东西需要维护一份跟着它走的扁平视图。一条 $N$ 节点链的标签拼接是 $O(N)$ 的字符串连接，所以总量仍是 $O(V)$。

## 顺序执行（`RuntimeEngine.RunAsync`）

`RunAsync`（第 52-128 行）一趟一趟地遍历图的分段；每个分段的代价是它驱动节点的总和：

| 分段 | 代价 |
|---|---|
| `ChainSegment` | $O(N_{\text{chain}})$ —— 对线性分段走一遍，逐个 await `ReceiveAsync` 并写 `context.Data` |
| `BranchSegment` | $O(N_{\text{branch}})$ —— 静态分支靠编译期锁定的 `CompileKey` 以 $O(1)$（选项扫描）选中；动态分支要付一次 `ResolveRouteKey` 加一次对 `Options` 的线性扫描 |
| `ParallelSegment` | $\sum_{\text{分支}} O(N_{\text{分支}})$ —— 分支**并发启动**，但只有 I/O 密集的分支才真能省墙钟时间，因为它们共用一条线程 |

每个 `DriveAsync`（第 412-506 行）是 $O(1)$ 的记账加上节点自身的工作：向 `IRuntimeAware` 节点注入会话、写 `CurrentOrder`；当节点是多输入汇合点时，它调 `CollectGroupedInputs` 把各输入装箱成 `IGroupData` —— 按已登记的输入来源建字典，$O(\text{输入数})$，预分配以避免重分配。

整张图、驱动 $N$ 个节点：

$$
T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)
$$

以节点数为准（墙钟时间由节点自身的工作量主导，例如 demo 里的 `Task.Delay`）。

### 带上限的扇出

$B$ 条分支、上限 $c$ 的 `ParallelSegment` 分 $\lceil B/c \rceil$ 波跑完；信号量每条分支 $O(1)$（一次 `WaitAsync` / `Release`）：

$$
T_{\text{扇出}} = \frac{1}{c}\sum_{j=1}^{B} T_{\text{分支}}(j) \quad (\text{受 } \lceil B/c \rceil \text{ 波约束}), \qquad S_{\text{扇出}} = O(B)
$$

`c = null` 意味着 $c = B$（完全重叠）；`c = 1` 退化成顺序代价。空间是每分支一个 `BranchRuntimeContext` 的数组，加每分支一个 `Task<bool>` —— 注意**所有 $B$ 个任务都是一次性建出来的**（`new Task<bool>[count]`），所以上限约束的是并发*工作*，不是已启动的任务数。

### 重定向

重定向朝目标 Order 重跑整张图，跳过契约保留的前缀（`Order < target`）；最多 50 次（`MaxRedirects`）：

$$
T_{\text{重定向}} = O(50 \cdot N)
$$

每一趟还要重走一遍分段列表，所以常数里还含分段数。

## 检查点

| 操作 | 时间 | 空间 |
|---|---|---|
| `ExecutionCheckpoint.NodesOf(graph)`（每轮一次） | $O(V)$ | $O(V)$ |
| `RuntimeContext.Snapshot()`（每次成功之后） | $O(R)$ —— $R$ = 已登记产物数，≤ $V$ | $O(R)$ |
| `InMemoryCheckpointStore.SaveAsync` | $O(1)$（锁下一次引用替换） | 保留 $O(R)$ |
| `FileCheckpointStore.SaveAsync` | $O(R)$ —— JSON 写入，在信号量后串行 | $O(R)$ |
| `RequireSameShape`（每次恢复一次） | $O(\min(V, |\text{Shape}|))$ | $O(1)$ |
| `Restore`（每次恢复一次） | $O(V)$ | $O(V)$ |
| `ExecutionCheckpoint.Rekey`（宿主调用） | $O(V + R)$ | $O(V + R)$ |

快照的代价正是检查点写在**每个节点之后**而不是每趟之后的原因：单节点 $O(R)$，而不是整体重算时的 $O(V) \cdot$ 节点数。

载荷很大时 `Snapshot()` 在规模化下并不便宜：它存下每个已完成节点的产物，而对汇合载荷它要把 `IGroupData` 改写成普通字典，每个组载荷 $O(\text{输入数})$。

## 宿主能力的开销

每个接缝都是一次 `null` 检查，加上（配置了时）一次调用。驱动 $N$ 个节点：

| 接缝 | 配置后每节点代价 |
|---|---|
| `IExecutionGate` | $O(1)$ —— 开着的门只做一次 `IsCompleted` 检查（不分配、不写 `Status`）；只在关着时等一个 `TaskCompletionSource` |
| `IExecutionObserver` | 每个成功节点 2 次调用（`NodeStarted`、`NodeSucceeded`）+ 每分支 1 次 + 每轮 2 次 |
| `INodeRetryPolicy` | **每次抛出的异常** 1 次调用，外加一次 `Task.Delay` |
| `IExecutionErrorSink` | 每次失败 1 次调用；节点抛出是 2 次（节点自己的记录，然后引擎的决定） |
| `IExecutionCheckpointStore` | 每个成功节点 1 次快照 + 1 次保存 |
| `IExecutionCompensation` | 每个成功驱动的节点 1 次调用，但**只在**结局是 `Failed` 或 `Cancelled` 时 —— 完成的运行是 0 次 |
| `ILogWriter` | 每行 $O(1)$，在 `AppendLog` 里 —— 计入节点自身的工作量 |

全部不设置时，额外总代价是 $N$ 次 `null` 检查：运行的表现与这一层存在之前一模一样，这就是它承诺的契约。

### 有界与无界的日志

默认 `Logs` 每行按 $O(1)$ 增长。设 `MaxRetainedLogs = m` 时，`AppendLog` 里的保留裁剪是：

$$
T_{\text{裁剪}} = \text{每行摊还 } O(1), \qquad S_{\text{Logs}} = O(m)
$$

因为每次调用最多加一行，最多需要一次 `RemoveAt(0)` —— `while` 循环只跑一次。`SnapshotLogs()` 是 $O(|\text{Logs}|)$ 并分配一个数组，也是唯一被认可跨线程读 `Logs` 的方式。

## 内存占用汇总

| 结构 | 空间 | 依据 |
|---|---|---|
| `CompiledGraph` + 分段 | $O(V + E)$ | 分段树 + visited 集合 + 锥 |
| `CompiledOutline` 行 | $O(E_s)$ | 每分段一行 |
| 运行时产物登记表 | $O(\text{被驱动节点})$ | 带趟戳的 `RegisterOutput` 表 |
| 本轮已完成列表（供补偿） | $O(\text{成功数})$ | 每节点一条，重驱动时移动而不是重复 |
| 扇出分支上下文 | $O(B)$ | 每分支一个 `BranchRuntimeContext` 加一个任务 |
| `ExecutionCheckpoint` | $O(V + R)$ | shape + types + outputs |
| `Logs` | $O(\text{行数})$，或上限 $O(m)$ | `ObservableCollection<string>` + 可选裁剪 |
| 序列化图快照 | $O(P_{\text{graph}})$ | 写入器停在图的边界上 |

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| 编译（`CompilerViewModel`，Root / Terminal） | $O(V+E)$ | $O(V+E)$ | 带记忆的分解 + 反向锥 + visited |
| `CompiledOutline.Of` | $O(V + E_s)$ | $O(E_s)$ | 一次深度优先，只算一次 |
| 执行分段（`RuntimeEngine`） | $O(N)$ | $O(N)$ | 对分段走一遍；汇合聚合 $O(\text{输入数})$ |
| 上限 $c$ 的 $B$ 分支扇出 | $\lceil B/c \rceil$ 波 | $O(B)$ | 每组一个信号量，任务一次性建出 |
| 重定向最坏 | $O(50 \cdot N)$ | $O(N)$ | `MaxRedirects = 50` |
| 快照 + 保存一次检查点 | $O(R)$ | $O(R)$ | 每个成功节点 |
| 恢复（`RequireSameShape` + `Restore`） | $O(V)$ | $O(V)$ | 形状比对 + 产物重登记 |
| 宿主能力全不设置 | $O(N)$ 次 `null` 检查 | $O(1)$ | 精确等于 2026-09-27 之前的行为 |
