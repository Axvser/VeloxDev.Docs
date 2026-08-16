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

## 编译（CompilerViewModel）

`CompilerViewModel.CompileAsync` 从起点做一次有记忆的分解：`CompileState.Visited` 保证每个节点只处理一次；对每个节点枚举其输出槽的 `Targets`（边）。设 $V$ 个节点、$E$ 条边（连接）：

$$T_{\text{compile}} = O(V + E)$$

分解是线性的（单出单入节点并入当前链）加路由点展开（`ICompileTimeRouter` 的每个 key 递归编译一个子图），每个节点仅访问一次，因此整体仍是 $O(V + E)$。静态模式下被剪枝分支会从起点沿拓扑走一遍发放「重置信号」（`Order = -1`），同样受 `Visited` 守卫，最多一次。空间为 $O(V + E)$（编译图条目 + 访问集）。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`，`CompileGraphAsync` 第 36-157 行、`FlushChain` 第 160-169 行、`MarkStoppedBranch` 第 186-200 行。*

## 顺序执行

`CompilerEngine.RunAsync` 恰好遍历一张图的条目，`ExecuteEntry` 逐个等待节点 `ReceiveAsync` 的返回值并写入 `RuntimeContext.Data` 链式传递。设图中节点数为 $N$：

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

在节点数量上（墙钟时间由节点工作负载主导，例如演示中的 `Task.Delay(DelayMilliseconds)`）。未选中的静态分支不会被驱动（`BranchEntry` 按 `CompileKey` 选择、`Order < 回退目标` 的节点被跳过）。`ParallelEntry` 扇出是顺序执行的（共享 `RuntimeContext` 黑板非线程安全，不做真并行）。跨链回退会带目标 Order 重跑整张图，最多 50 次（`MaxRedirects`），因此最坏情况 $T_{\text{redirect}} = O(50 \cdot N)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`，`RunGraphAsync` 第 63-89 行、`RunExecuteAsync` 第 96-148 行、`RunParallelAsync` 第 189-196 行。*

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
| 编译（CompilerViewModel） | $O(V+E)$ | $O(V+E)$ | 有记忆分解 + 访问集 |
| 执行链（CompilerEngine） | $O(N)$ | $O(N)$ | 单遍条目；回退最坏 $O(50N)$ |
| 撤销 / 重做 | 每个操作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | $O(1)$ 期望 | $O(\text{成员数})$ | 字典查找 |
