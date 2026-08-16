# 复杂度分析 — 工作流系统

使用 KaTeX 表示渐近界。每个结论都基于所引源码。

## 空间索引（`SpatialGridHashMap<T>`）

`SpatialGridHashMap<T>` 把平面按固定边长 $s$（`cellSize`）划分为单元。每个项目被哈希进它覆盖的单元；视口查询只枚举视口触碰的单元（`GetCells` / `CellEnumerator`，第 190-256 行）。

插入、移除和（属性变化时的）重索引每个项目只触碰有界的单元数 —— 对典型节点尺寸近似常数：

$$T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)$$

对宽度 $W$、高度 $H$ 的视口查询会访问 $k$ 个单元并过滤其中的项目：

$$k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)$$

其中 $m$ 是这些单元中的项目数。由于映射通过 `_queryScratch` 去重，每个不同项目只被输出一次（`SpatialGridHashMap.Query`，第 80-104 行）。最坏情况：所有项目集中到一个单元，退化为 $O(n)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SpatialGridHashMap.cs`。*

## 空间虚拟化（`WorkflowSpatialEx.Virtualize`）

`Virtualize` 执行两次空间查询 —— `QueryAgentBounds(viewport, expansionDepth: 1)`（节点对 provider）与 `QueryNodes(viewport)` —— 然后原地调整 `VisibleItems` 集合（`VirtualizeCore`，第 113-169 行）。设访问 $k_{\text{pair}}$ / $k_{\text{node}}$ 个单元，其中 $m$ 个项目：

$$T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)$$

其中 $v$ 是从可观察集合增删的项目数（受可见集约束）。深度 1 的展开经由反向索引为每个直接可见对行走其两个端点节点的相连对（`WorkflowSpatialManager.QueryAgentBounds`，第 75-116 行），每个可见节点增加 $O(\text{度})$ 工作量。期望情况下典型视口覆盖 $O(1)$ 个单元，因此整个流程期望为 $O(m + v)$。可重入由 `Virtualizing` 每树标志守卫，嵌套调用以 $O(1)$ 退出。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`、`Src/Core/VeloxDev.Core/WorkflowSystem/WorkflowSpatialManager.cs`。*

## 编译（`CompilerViewModel.CompileAsync`）

`CompileAsync` 从起点做一次有记忆的分解：`CompileState.Visited` 保证每个节点只处理一次；对每个节点枚举其输出槽的 `Targets`（边）。设 $V$ 个节点、$E$ 条边（连接）：

$$T_{\text{compile}} = O(V + E)$$

分解是线性的（单出单入节点并入当前链）加路由点展开（`ICompileTimeRouter` 的每个 key 递归编译一个子图），每个节点仅访问一次，因此整体仍是 $O(V + E)$。静态模式下被剪枝分支会从起点沿拓扑走一遍发放「重置信号」（`Order = -1`），同样受 `Visited` 守卫，最多一次。空间为 $O(V + E)$（编译图条目 + 访问集）。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`，`CompileGraphAsync` 第 36-157 行、`FlushChain` 第 160-169 行、`MarkStoppedBranch` 第 186-200 行。*

## 顺序执行（`CompilerEngine.RunAsync`）

`RunAsync` 遍历一张图的条目；每个条目的代价是其所驱动节点的总和：

| 条目 | 代价 |
|---|---|
| `ExecuteEntry` | $O(N_{\text{chain}})$ —— 对线性段单遍执行，逐个等待 `ReceiveAsync` 并写 `context.Data` |
| `BranchEntry` | $O(N_{\text{branch}} + B)$ —— $B$ = 扫描选项以找到所选 key 的个数，然后运行所选子图 |
| `ParallelEntry` | $\sum_{\text{branches}} O(N_{\text{branch}})$ —— 各分支**顺序**执行（共享 `RuntimeContext` 黑板非线程安全，不做真并行） |

整张图共驱动 $N$ 个节点：

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

在节点数量上（墙钟时间由节点工作负载主导，例如演示中的 `Task.Delay(DelayMilliseconds)`）。未选中的静态分支不会被驱动（`BranchEntry` 按 `CompileKey` 选择、`Order < 回退目标` 的节点被跳过）。跨链回退会带目标 Order 重跑整张图，最多 50 次（`MaxRedirects`），因此最坏情况 $T_{\text{redirect}} = O(50 \cdot N)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`，`RunGraphAsync` 第 63-89 行、`RunExecuteAsync` 第 96-148 行、`RunParallelAsync` 第 189-196 行。*

## 撤销 / 重做栈

每个变更操作把一个 `IWorkflowActionPair` 压入撤销栈。设 $n$ 个操作：

$$T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)$$

`UndoCommand` 以 $O(1)$ 弹出并运行常数工作量的操作，因此撤销 $k$ 个操作花费 $O(k)$。两个栈都是 `ConcurrentStack<IWorkflowActionPair>`。批处理操作（如 `StandardRemoveConnections`）把许多微操作聚合到一个操作对中，使栈深与逻辑用户操作数成正比。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，`TreeCache` 第 655-660 行、`StandardRemoveConnections` 第 430-528 行。*

## 选择器查找（`SlotEnumerator.TrySelect`）

`TrySelect` 是在条件映射上的字典查找，该映射在项目增删时增量维护：

$$T_{\text{TrySelect}} = O(1) \text{ 期望}$$

`SetSelector` 重建项目列表与条件映射，提交一个可撤销的 `WorkflowActionPair`；重建每次选择器切换花费 $O(\text{枚举成员数})$。`ConditionalSlot` 包装每个槽位；延迟移除惰性冲刷，使重入的集合变化分摊为 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`，`TrySelect` 第 255-258 行、`SetSelector` 第 260-382 行。*

## 序列化（`ComponentModelEx.Serialize` / `Deserialize`）

`JsonConvert.SerializeObject` 做一次图遍历。在 `PreserveReferencesHandling.Objects` 下，每个对象只访问一次并分配引用 id，因此遍历与序列化对象/属性总数成线性。设 $P$ = 序列化的对象 + 属性总数（上界 $O(V + E + \text{自定义属性})$，$V$ 节点、$E$ 连接）：

$$T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)$$

两个值得注意的常数因素：

- `WritablePropertiesOnlyResolver` 过滤为只写属性，从而减小 $P$（只读成员如 `Helper` 被跳过）（`ComponentModelEx.cs`，第 440-486 行）。
- `DictionaryKeyConverter` 用引用 id 写接口键字典（`LinksMap` 使用 `IWorkflowSlotViewModel` 键），每个字典条目 $O(1)$；读取时经 `ReferenceResolver` 解析每个键（`ComponentModelEx.cs`，第 381-438 行）。

设置（及其解析器的 Newtonsoft 契约缓存）被静态缓存，因此重复调用不会重新反射类型系统（`ComponentModelEx.cs`，第 56-102 行）。异步重载仍会在内存中物化完整 JSON 字符串 / 字节数组，因此内存占用为：

$$S_{\text{json}} = O(P \cdot \text{每个值的平均字节数})$$

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。*

## 内存占用汇总

| 结构 | 空间 | 依据 |
|---|---|---|
| `SpatialGridHashMap<T>` | $O(n \cdot c)$ —— $n$ 个项目，每个在 $c$ 个覆盖单元 | 单元哈希集合 |
| `WorkflowSpatialManager` | $O(V + E)$ —— 节点 provider + 节点对 provider + 反向索引 | 字典 |
| 撤销 / 重做栈 | $O(n)$ —— $n$ 个已提交操作对 | `ConcurrentStack` |
| `CompiledGraph` + 条目 | $O(V + E)$ | 条目 + 访问集 |
| 序列化 JSON | $O(P)$ —— 序列化总大小 | Newtonsoft 字符串 |

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ 期望 | 总计 $O(n \cdot c)$ | 每个项目单元有界 |
| `SpatialGridHashMap.Query` | $O(k + m)$ | 临时 $O(1)$ | $k$ = 视口内单元数 |
| `WorkflowSpatialEx.Virtualize` | 期望 $O(m + v)$ | 临时 $O(1)$ | 两次空间查询 + 可见集调整 |
| 编译（CompilerViewModel） | $O(V+E)$ | $O(V+E)$ | 有记忆分解 + 访问集 |
| 执行链（CompilerEngine） | $O(N)$ | $O(N)$ | 单遍条目；回退最坏 $O(50N)$ |
| 撤销 / 重做 | 每个操作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | $O(1)$ 期望 | $O(\text{成员数})$ | 字典查找 |
| `ComponentModelEx.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | Newtonsoft 图遍历（PreserveReferences） |
