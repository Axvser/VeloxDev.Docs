# 工作流系统 — 编辑器与空间一侧的复杂度

渐近界用 KaTeX 给出；每个数字都有源码出处。

## 空间索引（`SpatialGridHashMap<T>`）

`SpatialGridHashMap<T>` 把平面切成边长为 $s$ 的固定格子。每个元素被哈希进它覆盖的每个格子（`IndexItem` 遍历 `GetCells(bounds)`）；视口查询只枚举视口触及的格子（`Query` 第 94-125 行，`CellEnumerator` 第 317-367 行）。

插入、移除与（属性变更触发的）重建索引对每个元素只碰有界数量的格子 —— 对典型节点尺寸实际是常数：

$$
T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)
$$

宽度 $W$、高度 $H$ 的视口查询会访问 $k$ 个格子并过滤其中的元素：

$$
k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)
$$

其中 $m$ 是这些格子里的元素数。`_queryScratch` 去重，保证每个不同元素只被吐出一次，且每个元素的边界要与视口做实际相交测试（`IntersectsWith`/`Contains`）。最坏情况：所有元素塌进同一个格子，退化成 $O(n)$。一个重入守卫会把重建过程中触发的网格变更延后、最后统一再同步一次（`_rerunPending` + `ResyncGrid`），因此嵌套的缩放级联摊还下来每次变更是 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs`。*

## 空间虚拟化（`WorkflowSpatialEx.Virtualize`）

`Virtualize`（第 97-115 行）是 `VirtualizeCore`（第 117-190 行）外面一层带重入守卫的包装；内核做 `manager.QueryAgentBounds(query, expansionDepth: 1)`（节点对提供者）加 `manager.QueryNodes(query)`，构建目标集合，并就地调和 `VisibleItems`。设访问了 $k_{\text{pair}}$ / $k_{\text{node}}$ 个格子、这些格子里有 $m$ 个元素：

$$
T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)
$$

其中 $v$ 是从可观察集合里增删的元素数（有界于可见集合）。深度 1 的展开会为每个直接可见的节点对，经反向索引走它两个端点节点相连的节点对（`WorkflowSpatialManager.QueryAgentBounds` 第 79-124 行），每个可见节点追加 $O(\text{度})$ 的工作。期望情况下典型视口覆盖 $O(1)$ 个格子，所以整趟是期望 $O(m + v)$。嵌套的 `Virtualize` 调用经每棵树的 `Virtualizing` 标志以 $O(1)$ 退出。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`、`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`。*

## 撤销 / 重做栈

每个变更操作把一个 `IWorkflowActionPair` 压入撤销栈。设 $n$ 个动作：

$$
T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)
$$

`StandardUndo`/`StandardRedo` 以 $O(1)$ 弹出并执行一个常数工作量的动作。两个栈都是每棵树 `TreeCache` 里的 `ConcurrentStack<IWorkflowActionPair>`。像 `StandardRemoveConnections` 这样的批量操作会把许多微操作聚合成一对，使栈深与逻辑用户动作数成正比。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，`StandardSubmit` 第 208-220 行，`StandardRemoveConnections` 第 428-526 行，`TreeCache` 第 653-658 行。*

## 选择器查找（`SlotEnumerator.TrySelect` / `SetSelector`）

`TrySelect` 是对条件映射的字典查找，该映射在增删条目时增量维护：

$$
T_{\text{TrySelect}} = O(1) \text{ expected}
$$

`SetSelector`（第 260-382 行）为新的枚举/布尔/`ISlotProvider` 类型重建条目列表与条件映射，并提交一个可撤销的 `WorkflowActionPair`；重建的代价是每次切换 $O(\text{枚举成员数})$。延后的移除惰性刷出，因此重入的集合变更摊还仍是 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`，`TrySelect` 第 255-258 行。*

## 序列化（`ComponentModelEx.Serialize` / `Deserialize`）

`JsonConvert.SerializeObject` 做的是一次图遍历。开着 `PreserveReferencesHandling.Objects` 时，每个对象只被访问一次并分配一个引用 id，所以遍历对「被序列化的对象/属性数」是线性的。设 $P$ = 被序列化的对象 + 属性总数（有界于 $O(V + E + \text{自定义属性})$，$V$ 个节点、$E$ 条连线）：

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

三个值得注意的常数因子：

- `WritablePropertiesOnlyResolver` 只保留可写属性，减小 $P$（`Helper` 这类只读成员被跳过）（`ComponentModelEx.cs` 第 459-518 行）。
- `DictionaryKeyConverter` 按引用 id 写以接口为键的字典（`LinksMap` 用 `IWorkflowSlotViewModel` 做键），每个字典条目 $O(1)$；读入时经 `ReferenceResolver` 解析每个键（`ComponentModelEx.cs` 第 400-457 行）。
- **编译图快照是刻意更小的。** `CompiledGraphEx.SerializeCompiledGraph(graph, includeTree: false)` 排除 `IWorkflowTreeViewModel` 与 `ObservableCollection<IWorkflowSlotViewModel>` 属性，写入器因此绝不顺着 `Parent` 走进树、也不顺着槽位的 `Targets`/`Sources` 走进整个连通分量。代价从「整棵树加它的连通分量」降到分段结构加每个节点自身的状态 —— 代价是还原出来的节点不可重新上墙。

设置（以及其 resolver 的 Newtonsoft 契约缓存）是静态缓存的，重复调用不会重新反射类型系统（`ComponentModelEx.cs` 第 71-121 行）。反序列化会先按序列化下来的 `SelectorTypeName` 重新解析 `SlotEnumerator` 的选择器类型，消费方再重新抛出派生值。异步重载仍然会把完整 JSON 字符串 / 字节数组物化在内存里，所以内存是：

$$
S_{\text{json}} = O(P \cdot \text{avg bytes per value})
$$

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`、`CompiledGraphEx.cs`。*

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | 期望 $O(1)$ | 合计 $O(n \cdot c)$ | 每个元素碰有界个格子 |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ 临时 | $k$ = 视口内格子数 |
| `WorkflowSpatialEx.Virtualize` | 期望 $O(m + v)$ | $O(1)$ 临时 | 两次空间查询 + 可见集合调和 |
| 撤销 / 重做 | 每个动作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | 期望 $O(1)$ | $O(\text{成员数})$ | 字典查找 |
| `ComponentModelEx.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | Newtonsoft 图遍历（PreserveReferences） |
| `CompiledGraphEx.SerializeCompiledGraph`（快照） | $O(P_{\text{graph}})$ | $O(P_{\text{graph}})$ | 写入器停在图的边界上 |
