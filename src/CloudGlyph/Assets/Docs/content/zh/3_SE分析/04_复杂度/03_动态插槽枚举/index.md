# 动态插槽枚举

`SlotEnumerator<TSlot>` 维护一张从选择器值到插槽的 `Dictionary<object, TSlot>`，所以按运行值选择是常数时间。代价在于*切换*选择器：旧分支集被拆除，新分支集被物化，然后逐分支重连连线。该重连是唯一的超线性步骤，按名称匹配分支时呈二次。

记号：$E$ 个枚举成员或提供方定义，上一分支集 $E_{\text{prev}}$ 个分支，度 $d$，树的连线 $L$，所属节点的插槽 $S$，提供方 $P$，延迟移除 $R$。

## 代价模型

| 操作 | 时间 | 出处 |
|---|---|---|
| `TrySelect` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:279` |
| `SetSelector`，枚举，全新构建 | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:285` |
| `SetSelector`，提供方，全新构建 | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:300` |
| `SetSelector`，类型已缓存 | $O(1)$ 查表 + $O(E+L)$ 应用 | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:401` |
| 切换前布线快照 | $O(E d + L)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:372` |
| `ApplyAttachedState` | $O(L + E + E S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:551` |
| `ApplyNewState` 重连 | 按名称 $O(E^2)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:439` |
| 批量添加 $n$ 项 | 最坏 $O(n^2)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:96` |
| `FlushDeferredRemovals` | 均摊 $O(R n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:260` |
| `Install` / `Uninstall` | $O(P)$ / $O(E+P)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:675` |

路由查找只是一次字典探测：

```csharp
public bool TrySelect(object value, out TSlot? slot)
{
    return conditionMap.TryGetValue(value, out slot);
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:279-282`

## 重建分支集

`SetSelector` 先捕获当前布线——每项的 `Targets` 与 `Sources` 数组，以及触及当前插槽的那部分树连线。该快照对分支数乘度加树连线是线性的。随后替换项，并把每个新分支重连到它所替换分支的邻居：

```csharp
for (int i = 0; i < state.Items.Count; i++)
{
    var branch = state.Items[i].Slot;
    var previous = MatchBranch(previousWiring, state.Items[i].Name, i, byName);
    ...
    foreach (var receiver in previous.Value.Targets)
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs:439-445`

选择器类型相同时按名称匹配，`MatchBranch` 是对上一集合的线性搜索；类型不同时按位置匹配，是下标访问。按名称匹配使整个重连步骤呈二次：

$$
T_{\text{apply}}(E) = O(E^2 + E\,d + L)
$$

```plot
{
  "title": "分支重连：按位置与按名称",
  "grid": true,
  "xAxis": { "domain": [0, 60] },
  "yAxis": { "domain": [0, 3600] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "按位置匹配，O(E)" },
    { "fn": "x*x", "color": "#f472b6", "title": "按名称匹配，O(E^2)" }
  ]
}
```

## 重复值与延迟移除

添加一项时先做 $O(1)$ 的值映射检查，然后扫描 `Items` 找过期重复项，即每次添加 $O(E)$、批量添加 $O(n^2)$。在集合变更回调中移除项会延迟到一个列表，惰性刷新；每次刷新对当前项数线性。

## 内存

每个分支通常花费一个 `ConditionalSlot<TSlot>` 加一个 `TSlot`。在提供方路径上，枚举器为每个定义分配**两个**插槽——`ConditionalSlot` 预先构造一个，`SetSelector` 又用一个新构造的插槽覆盖它。更大的保留来自按类型的状态缓存：`_typeStates` 为每个用过的选择器类型保留完整的 `SelectorState`（项列表与连线数组），且从不淘汰，所以内存为枚举器生命周期内的 $O(\sum_E \text{项} + \sum_E \text{连线})$。延迟移除列表是瞬时的。
