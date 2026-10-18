# 工作流系统 — 编辑器与空间侧的复杂度

渐近界使用 KaTeX；每个数字都落在所引源码上。

## 空间索引（`SpatialGridHashMap<T>`）

`SpatialGridHashMap<T>` 把平面划分为边长固定为 $s$ 的网格。每个条目会哈希进它覆盖的每个单元（`IndexItem` 遍历 `GetCells(bounds)`）；视口查询只枚举视口触及的单元（`Query` 94-125 行，`CellEnumerator` 317-367 行）。

插入、删除与（属性变化触发的）重建索引每个条目都只触及有界数量的单元 —— 对典型节点尺寸实际上是常数：

$$
T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)
$$

对宽 $W$、高 $H$ 的视口查询，访问 $k$ 个单元并过滤其中的条目：

$$
k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)
$$

其中 $m$ 是这些单元内的条目数。`_queryScratch` 去重，保证每个不同条目只输出一次，并且每个条目的边界都与视口做 `IntersectsWith`/`Contains` 测试。最坏情况：所有条目挤进一个单元，退化为 $O(n)$。重入守卫会推迟重建索引期间触发的网格变更并在之后重同步一次（`_rerunPending` + `ResyncGrid`），使嵌套缩放级联每次变更摊还 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs`。*

## 空间虚拟化（`WorkflowSpatialEx.Virtualize`）

`Virtualize`（97-115 行）是围绕 `VirtualizeCore`（117-190 行）的重入守卫包装：后者执行 `manager.QueryAgentBounds(query, expansionDepth: 1)`（节点对 provider）加 `manager.QueryNodes(query)`，构建期望条目集并就地调和 `VisibleItems`。设访问 $k_{\text{pair}}$ / $k_{\text{node}}$ 个单元、这些单元内有 $m$ 个条目：

$$
T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)
$$

其中 $v$ 是可观察集合中增删的条目数（以可见集为界）。深度 1 扩展会对每个直接可见的节点对，经反向索引走过其两个端点节点的相连节点对，每个可见节点增加 $O(\text{degree})$ 工作。期望情况：典型视口覆盖 $O(1)$ 个单元，整趟期望 $O(m + v)$。嵌套 `Virtualize` 调用通过每棵树的 `Virtualizing` 标志在 $O(1)$ 内退出。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`、`WorkflowSpatialManager.cs`。*

## 撤销 / 重做栈

每个变更操作向撤销栈压入一个 `IWorkflowActionPair`。设 $n$ 个动作：

$$
T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)
$$

`StandardUndo`/`StandardRedo` 以 $O(1)$ 弹出并运行常数工作量的动作。两个栈都是每棵树 `TreeCache` 中的 `ConcurrentStack<IWorkflowActionPair>`。`StandardRemoveConnections` 这类批操作把多个微动作聚合成单个对，使栈深度与逻辑用户动作成正比。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`（`StandardSubmit`、`StandardRemoveConnections`、`TreeCache`）。*

## 选择器查找（`SlotEnumerator.TrySelect` / `SetSelector`）

`TrySelect` 是条目增删时增量维护的条件映射上的字典查找：

$$
T_{\text{TrySelect}} = O(1) \text{ expected}
$$

`SetSelector` 为新枚举/bool/`ISlotProvider` 类型重建条目列表与条件映射，并提交一个可撤销 `WorkflowActionPair`；每次选择器切换的重建代价为 $O(\text{enum members})$。延迟移除惰性冲刷，使可重入集合变更保持摊还 $O(1)$。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`。*

## 连接拖拽的槽命中测试（`SlotHitTestEx.HitTest`）

连接拖拽进行时，适配器调用 `SlotHitTestEx.HitTest(tree, x, y, radius)` 询问指针下是哪个槽锚点。实现是对所有节点、所有槽的全量扫描，不查询空间索引：

$$
T_{\text{slotHit}} = O\left(\sum_{i=1}^{V} |\text{slots}(i)|\right), \qquad S_{\text{slotHit}} = O(1)
$$

每个已测量锚点花费一次减法、两次乘法与一次比较（$dx^2 + dy^2$）；未测量锚点（`NaN`）被跳过。重叠槽取最近锚点，相等时保留先遇到的。这刻意比走 `SpatialGridHashMap` 简单：拖拽是短暂的、指针频率的手势，而图的槽数相对空间索引所服务的节点工作量很小。超大的图（数万槽）会让每次指针移动变成线性；逃生通道是由宿主侧的空间查询直接把结果喂给 `StandardSetPreviewReceiver`。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/SlotHitTestEx.cs`（`HitTest` 29-56 行，`DefaultHitRadius = 12`）。测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs`（`SlotHitTest_FindsTheNearestMeasuredSlot`、`SlotHitTest_SkipsAnUnmeasuredAnchor`）。*

## 序列化（`ViewModelSerializer.Serialize` / `Deserialize`）

writer 通过**生成的** reader/writer 遍历对象图 —— 没有反射，因此也没有需要预热的运行时契约缓存。每个对象只访问一次：`VeloxJsonWriter.WriteStartObject` 给它一个对象 id，第二次遇到时写引用标记而不是再写一遍对象，这正是带 `Parent` 反向引用的图不会膨胀的原因。遍历与写入成员数成正比。设 $P$ = 写入成员数（以 $O(V + E + \text{custom members})$ 为界，$V$ 个节点，$E$ 条连线）：

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

三个值得注意的常数因子：

- **成员集合在编译期决定**，不是运行期过滤：生成器按声明顺序收集带 public setter 的 public 属性，然后是 `[VeloxProperty]` 字段。像 `Helper` 这样的只读成员从不是候选，也从不产生分支（`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:912-1025`）。
- **接口键映射**（`LinksMap` 以 `IWorkflowSlotViewModel` 为键）写为键的引用 id —— 每条 $O(1)$ —— 读取时通过 reader 的引用表解析回来（`Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:540,625`）。
- **编译图快照按设计更小。** `CompiledGraphEx.SerializeCompiledGraph(graph, includeTree: false)` 排除 `IWorkflowTreeViewModel` 与 `ObservableCollection<IWorkflowSlotViewModel>` 属性，所以 writer 从不沿 `Parent` 走进树，也不从槽的 `Targets`/`Sources` 走进整个连通分量。代价从「树加上它的连通分量」降到「分段结构加上每个节点自己的状态」—— 代价是恢复的节点无法重新挂载。

注册表查找无锁（`volatile` 字段背后的不可变快照），成员名就地比较而非驻留，所以两侧都不会为每个成员分配字符串（`Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:83-96`）。反序列化会先从序列化的 `SelectorTypeName` 重新解析 `SlotEnumerator` 的选择器类型，再让消费方重新抛出派生值。异步重载仍会在内存中物化完整 JSON 字符串/字节数组，所以内存占用是：

$$
S_{\text{json}} = O(P \cdot \text{avg bytes per value})
$$

*源码：`Src/Core/VeloxDev.Core/Serialization/`、`Src/Core/VeloxDev.Core.Extension/CompiledGraphEx.cs`。*

## 汇总表

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | 期望 $O(1)$ | 总计 $O(n \cdot c)$ | 每条目有界单元数 |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ 暂存 | $k$ = 视口内单元数 |
| `WorkflowSpatialEx.Virtualize` | 期望 $O(m + v)$ | $O(1)$ 暂存 | 两次空间查询 + 可见集调和 |
| 撤销 / 重做 | 每动作 $O(1)$ | $O(n)$ | 并发栈 |
| `SlotEnumerator.TrySelect` | 期望 $O(1)$ | $O(\text{members})$ | 字典查找 |
| `SlotHitTestEx.HitTest` | $O(\text{slots})$ | $O(1)$ | 遍历节点与槽的线性扫描 |
| `ViewModelSerializer.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | 生成遍历，每对象一次（id / 引用标记） |
| `CompiledGraphEx.SerializeCompiledGraph`（快照） | $O(P_{\text{graph}})$ | $O(P_{\text{graph}})$ | writer 在图边界停止 |
