# 复杂度分析 — 工作流系统

用 KaTeX 表示渐近界。每个结论都立足于所引源码。

## 空间索引（`SpatialGridHashMap<T>`）

`SpatialGridHashMap<T>` 把平面按固定边长 $s$（`cellSize`，下限钳为 1）划分为单元；每个项目被哈希进它覆盖的**每个**单元（`IndexItem` 第 212-223 行）。视口查询只枚举视口触碰的单元，并用 `_queryScratch` 去重、按真实相交再过滤（`Query` 第 82-106 行）。

插入、移除和（边界属性变化时的）重索引每个项目只触碰有界的单元数——对典型节点尺寸近似常数：

$$
T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)
$$

对宽度 $W$、高度 $H$ 的视口，查询访问 $k$ 个单元并过滤其中项目：

$$
k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)
$$

其中 $m$ 为这些单元里的项目数。最坏情况：所有项目塌缩进同一单元，退化为 $O(n)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs`。*

## 空间虚拟化（`WorkflowSpatialEx.Virtualize`）

`Virtualize` 做两次空间查询——`QueryAgentBounds(viewport, expansionDepth: 1)`（节点对 provider，沿反向索引做一层连接扩展）与 `QueryNodes(viewport)`——然后就地调和 `VisibleItems`（`VirtualizeCore` 第 119-192 行）。设访问 $k_{\text{pair}}$ / $k_{\text{node}}$ 个单元、其中 $m$ 个项目：

$$
T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)
$$

其中 $v$ 是从可见集增删的项目数。深度 1 扩展对每个直接可见对，经反向索引 `_nodeToPairs` 走其两端节点的相连对（`WorkflowSpatialManager.QueryAgentBounds` 第 79-120 行），每个可见节点增加 $O(\text{度})$ 工作量。期望情形典型视口覆盖 $O(1)$ 个单元，整体期望 $O(m + v)$。可重入由 `Virtualizing` 每树标志守卫，嵌套调用 O(1) 退出。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`、`GUI/Virtualization/WorkflowSpatialManager.cs`。*

## 编译（`CompilerViewModel.CompileAsync`）

`CompileAsync` 是一次有记忆的分解：`CompileState.Visited` 保证每个节点至多处理一次；对每个节点枚举其输出槽的 `Targets` 边，每条边跑一次 `AccessAsync` 静态校验。设 $V$ 个节点、$E$ 条连接：

$$
T_{\text{compile}} = O(V + E)
$$

分解是线性的（单入单出节点并入当前链；多输入边界把节点交还父图）+ 路由点展开（`ICompileTimeRouter` 的每个 key 递归编译一个子图；多目标扇出成 `ParallelSegment`），每个节点只访问一次，整体仍是 $O(V + E)$；边校验的 `AccessAsync` 每条边一次。静态模式被剪枝分支从起点沿拓扑行走发“重置信号”（`Order = -1`），同样受 `Visited` 守卫、至多一次。反向编译（`CompileRole.Terminal`）在祖先锥内再做一次反向 BFS（`BuildAncestorConeAsync`，每条反向边一次 `AccessAsync`）——锥内 $V_c$ 节点、$E_c$ 边，代价 $O(V_c + E_c)$，与锥外无关。空间 $O(V + E)$（编译图条目 + 访问集 + 锥集）。

*源码：`CompilerEx/Compile/CompilerViewModel.cs`——`CompileAsync` 第 37-57 行、`CompileGraphAsync` 第 59-232 行、`FlushChain` 第 235-244 行、`MarkStoppedBranch` 第 264-278 行、`GetValidTargetsAsync` 第 397-430 行；`CompilerEx/Compile/CompilerViewModel.Reverse.cs`——`BuildAncestorConeAsync` 第 33-74 行、`CompileConeAsync` 第 82-134 行。*

## 顺序执行（`RuntimeEngine.RunAsync`）

`RunAsync` 遍历一张图的条目；每 pass 的代价为其驱动节点的总和：

| 段 | 代价 |
|---|---|
| `ChainSegment` | $O(N_{\text{chain}})$——线性段单遍驱动，逐个等待 `ReceiveAsync` 并写 `context.Data`；跨链重定向时 `Order < target` 的节点跳过 |
| `BranchSegment` | $O(N_{\text{branch}} + B)$——$B$ = 扫描选项找到所选 key 的个数；无下游/终点分支立刻终止 |
| `ParallelSegment` | $\sum_{\text{branches}} O(N_{\text{branch}})$——各分支**顺序**执行（共享 `IRuntimeContext` 黑板非线程安全，不做真并行）；每条分支前以 O(1) 恢复扇出源负载 |

汇合注入：当编译期登记的 `InputNodes.Count > 1`，引擎在驱动前把 `Data` 替换为 `GroupData`（`CollectGroupedInputs` 构造只读字典，容量按输入源数预分配，$O(k_{\text{in}})$；`IsCurrentPassOrPreserved` 每条 O(1)）。

整图共驱动 $N$ 个节点：

$$
T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)
$$

以节点数计（墙钟时间由节点工作负载主导，如演示 Python 节点的 30s 子进程超时、Agent 的 LLM 调用）。未选中的静态分支不会被驱动（`BranchSegment` 按 `CompileKey`/运行期 key 选，`Order = -1` 的停止节点不驱动）。跨链回退会以目标 Order 重跑整图、至多 50 次（`MaxRedirects`），最坏 $T_{\text{redirect}} = O(50 \cdot N)$（重定向重跑不清空产物登记表，陈旧产物按 pass 戳过滤）。

*源码：`CompilerEx/Runtime/RuntimeEngine.cs`——`RunAsync` 第 19-68 行、`RunGraphAsync` 第 71-97 行、`RunExecuteAsync` 第 106-160 行、`RunBranchAsync` 第 167-196 行、`RunParallelAsync` 第 205-214 行、`DriveAsync` 第 227-261 行。*

## 撤销 / 重做栈

每个变更操作把一对 `IWorkflowActionPair` 压入撤销栈。设 $n$ 个操作：

$$
T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)
$$

`UndoCommand` 以 O(1) 弹栈并运行常数工作量动作，撤销 $k$ 个操作花费 $O(k)$。两个栈都是每树 `ConcurrentStack<IWorkflowActionPair>`（`TreeCache`）。批处理操作（如 `StandardRemoveConnections`）把许多微操作聚合进单个操作对，栈深与逻辑用户操作数成正比。

*源码：`StandardEx/WorkflowTreeEx.cs`——`TreeCache` 第 655-660 行、`StandardRemoveConnections`（private）第 430-528 行。*

## 选择器查找（`SlotEnumerator.TrySelect`）

`TrySelect` 是对条件映射的字典查找，映射在条目增删时增量维护：

$$
T_{\text{TrySelect}} = O(1) \text{ 期望}
$$

`SetSelector` 重建条目表与条件映射并提交一个可撤销 `WorkflowActionPair`；重建代价 $O(\text{枚举成员数})$ 每次选择器切换。`ConditionalSlot` 包装每个槽位；延迟移除（`_deferredRemovals`）惰性冲刷，令重入集合变化分摊 O(1)。

*源码：`SelectorEx/SlotEnumerator.cs`——`TrySelect` 第 255-258 行、`SetSelector` 第 260-382 行。*

## 序列化（`ComponentModelEx.Serialize` / `Deserialize`）

`JsonConvert.SerializeObject` 做一次图遍历。`PreserveReferencesHandling.Objects` 下每个对象只访问一次并分配引用 id，遍历与序列化对象/属性总数成线性。设 $P$ = 序列化对象 + 属性总数（上界 $O(V + E + \text{自定义属性})$）：

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

值得注意的常数因素：`WritablePropertiesOnlyResolver` 过滤为只写属性（只读成员如 `Helper` 被跳过）；`DictionaryKeyConverter` 用引用 id 写接口键字典（`LinksMap` 用 `IWorkflowSlotViewModel` 键），每字典条目 O(1)，读取时经 `ReferenceResolver` 解析。设置及其解析器契约被静态缓存，重复调用不重新反射类型系统。异步重载仍在内存物化完整 JSON 字符串/字节数组：

$$
S_{\text{json}} = O(P \cdot \text{每值平均字节数})
$$

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。*

## 内存占用汇总

| 结构 | 空间 | 依据 |
|---|---|---|
| `SpatialGridHashMap<T>` | $O(n \cdot c)$——$n$ 个项目，各在 $c$ 个覆盖单元 | 单元哈希集 |
| `WorkflowSpatialManager` | $O(V + E)$——节点 provider + 节点对 provider + 反向索引 | 字典 |
| 撤销 / 重做栈 | $O(n)$——$n$ 个已提交操作对 | `ConcurrentStack` |
| `CompiledGraph` + 段 | $O(V + E)$ | 条目 + 访问集 |
| 序列化 JSON | $O(P)$——序列化总大小 | Newtonsoft 字符串 |

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ 期望 | 总计 $O(n \cdot c)$ | 每项目单元有界 |
| `SpatialGridHashMap.Query` | $O(k + m)$ | 临时 $O(1)$ | $k$ = 视口内单元数 |
| `WorkflowSpatialEx.Virtualize` | 期望 $O(m + v)$ | 临时 $O(1)$ | 两次空间查询 + 可见集调和 |
| 编译（`CompilerViewModel`，Root / Terminal） | $O(V + E)$ | $O(V + E)$ | 有记忆分解 + 访问/锥集 |
| 执行（`RuntimeEngine`） | $O(N)$ | $O(N)$ | 单遍段驱动；回退最坏 $O(50N)$；汇合 $O(k_{\text{in}})$ |
| 撤销 / 重做 | 每操作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | $O(1)$ 期望 | $O(\text{成员数})$ | 字典查找 |
| `ComponentModelEx.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | Newtonsoft 图遍历（PreserveReferences） |
