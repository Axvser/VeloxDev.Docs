# 复杂度分析 — 工作流系统

## 空间索引（SpatialGridHashMap）

`SpatialGridHashMap<T>` 把平面按固定边长 $s$（`cellSize`）划分为单元。每个项目被哈希进它覆盖的单元；视口查询只枚举视口触碰的单元。

插入、移除和（属性变化时的）重索引每个项目只触碰有界的单元数 —— 近似常数：

$$T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)$$

对宽度 $W$、高度 $H$ 的视口查询会访问 $k$ 个单元并过滤其中的项目：

$$k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)$$

其中 $m$ 是这些单元中的项目数。由于映射通过 `_queryScratch` 去重，每个不同项目只被输出一次。最坏情况：所有项目集中到一个单元，退化为 $O(n)$。

以单元尺寸 $s = 200$、典型节点尺寸而言，期望情况下一个视口覆盖 $O(1)$ 个单元，因此 `WorkflowSpatialEx.QueryNodes` 期望为 $O(k)$，其中 $k = O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SpatialGridHashMap.cs`，`GetCells`/`CellEnumerator` 第 190-256 行。*

## 编译（BFS / DFS）

编译器先从槽位 targets/sources 构建一次邻接表，再遍历。设 $V$ 个节点、$E$ 条边（连接）：

$$T_{\text{adjacency}} = O(V + E)$$

BFS 与 DFS 各自只访问每个节点一次（由 `globalVisited` 守卫）：

$$T_{\text{compile}} = O(V + E)$$

环路检测（`DfsFindCycle`）是对整个图的一次 DFS，也是 $O(V + E)$，无论有多少个 `Omni` 入口都只做一次。按 `CompilePriority` 排序同深度邻居会为每个节点增加 $O(\deg \log \deg)$ 的因子。空间为 $O(V + E)$（邻接表与访问集）。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Compilation/Compiler.cs`，`BuildForwardAdjacency` 第 153-174 行、`TraverseBfsFrom` 第 252-296 行、`TraverseDfsFrom` 第 300-336 行、`DetectCycle` 第 353-389 行。*

## 顺序执行

`CompilationResult.ExecuteAsync` 恰好遍历一次有序项目，逐个等待节点 `WorkCommand.Exited`。设编译项目数为 $N$：

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

在节点数量上（墙钟时间由节点工作负载主导，例如演示中的 `Task.Delay(DelayMilliseconds)`）。执行器通过 `HashSet<int>` 记录跳过的项目 ID，从而跳过未选中的路由器分支，循环不会重复执行节点。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Compilation/Models/CompilationResult.cs`，`ExecuteCoreAsync` 第 157-260 行。*

## 撤销 / 重做栈

每个变更操作把一个 `IWorkflowActionPair` 压入撤销栈。设 $n$ 个操作：

$$T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)$$

`UndoCommand` 以 $O(1)$ 弹出并运行常数工作量的操作，因此撤销 $k$ 个操作花费 $O(k)$。两个栈都是 `ConcurrentStack<IWorkflowActionPair>`。批处理操作（如 `StandardRemoveConnections`）把许多微操作聚合到一个操作对中，使栈深与逻辑用户操作数成正比。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，`TreeCache` 第 643-654 行、`StandardRemoveConnections` 第 418-516 行。*

## 选择器查找（SlotEnumerator.TrySelect）

`TrySelect` 是在条件映射上的字典查找，该映射在项目增删时增量维护：

$$T_{\text{TrySelect}} = O(1) \text{ 期望}$$

`SetSelector` 重建项目列表与条件映射，提交一个可撤销的 `WorkflowActionPair`；重建每次选择器切换花费 $O(\text{枚举成员数})$。`ConditionalSlot` 包装每个槽位；延迟移除惰性冲刷，使重入的集合变化分摊为 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`，`TrySelect` 第 132-135 行、`SetSelector` 第 137-226 行。*

## 汇总

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ 期望 | 总计 $O(n)$ | 每个项目单元有界 |
| `SpatialGridHashMap.Query` | $O(k + m)$ | 临时 $O(1)$ | $k$ = 视口内单元数 |
| 编译（BFS/DFS） | $O(V+E)$ | $O(V+E)$ | 单次遍历 + 邻接表 |
| 执行链 | $O(N)$ | $O(N)$ | 单遍项目 |
| 撤销 / 重做 | 每个操作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | $O(1)$ 期望 | $O(\text{成员数})$ | 字典查找 |
