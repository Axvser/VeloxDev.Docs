# 复杂度分析 — MVVM

## 生成的属性 setter（默认模式）

生成的 setter 无论值类型如何都执行常数次操作：

$$O(1)$$

步骤：`Object.Equals` 守卫、捕获 `old`、`OnPropertyChanging`、`OnXxxChanging`、字段赋值、`OnXxxChanged`、`OnPropertyChanged` — 全部常数时间。setter 体来源：`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`，`GetSetterBodyLines`，第 287-307 行。

对于 `INotifyCollectionChanged` 属性，替换集合时还会额外调用 `ObservableCollectionTracker.Unsubscribe(old, ...)` 和 `EnsureSubscribed(value, ...)`，并对被替换集合的条目调用 `OnItemRemovedFromXxx` / `OnItemAddedToXxx`：

$$O(k) \quad \text{其中 } k = |\text{旧集合}| + |\text{新集合}|$$

*$O(k)$ 的替换代价依据生成的集合 setter 行推断（`GetCollectionBeforeAssignmentLines` / `GetCollectionAfterAssignmentLines`，第 486-526 行）；非替换的 getter 路径为 $O(1)$。*

## CollectionChanged 处理器（每次变更）

生成的 `OnXxxCollectionChanged` 把原始事件转发给 `OnCollectionChanged<T>`（$O(1)$），并在 Add / Remove / Replace / Move 时通过 `EnumerateXxxItems` → `ToArray` 物化受影响的条目：

$$O(m) \quad \text{其中 } m \text{ 为受影响的条目数}$$

（`GenerateCollectionMembers`，第 575-700 行。）

## ObservableCollectionTracker.EnsureSubscribed

$$O(1) \text{ 均摊}$$

`ConditionalWeakTable.GetOrCreateValue` 加上 `HashSet<Delegate>` 添加（`Entry.TryAdd`，引用同一性比较）。每个集合首次调用时订阅，后续调用是快速的同一性查找。弱引用键意味着当集合被垃圾回收时跟踪条目自动消失 — 无泄漏。

（源：`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`，第 15-56 行。）

## 命令执行

容量可用时的正常执行：

$$O(1) \text{ 每次触发，均摊}$$

`ExecuteAsync` 执行 `SemaphoreSlim.WaitAsync` + `_active.Add` + fire-and-forget（VeloxCommand.cs，第 139-174 行）。容量耗尽时条目入队：

$$O(1) \text{ 入队, } \quad O(n) \text{ 最坏排队}$$

其中 $n$ 为排队条数。`TryStartPendingAsync` 排空最多 `_maxConcurrency` 个条目，整个排空过程 $O(n)$（第 349-377 行）；由于队列由完成中的调用排空，每次触发均摊为 $O(1)$。

`Notify()` → `RaiseCanExecuteChanged()` 为 $O(H)$，其中 $H$ 是已注册的 `CanExecuteChanged` 处理器数量（通常是一个绑定）。

## 内存使用

| 结构 | 复杂度 |
|---|---|
| 每个带注解类型的生成成员 | $O(P + C)$ 每类型常数；$P$ = `[VeloxProperty]` 字段数，$C$ = `[VeloxCommand]` 方法数 |
| `VeloxCommand` 状态 | $O(n)$ 活动 + 排队 `CommandEventArgs`，$n$ = 在途调用数 |
| `ObservableCollectionTracker` 表 | $O(C)$ 个被跟踪集合，经 `ConditionalWeakTable`（随集合回收） |
| 每次执行的 `CommandEventArgs` | $O(1)$ 瞬时 |

## 逐操作汇总

| 操作 | 复杂度 |
|---|---|
| 属性 get（非集合） | $O(1)$ |
| 属性 set（非集合） | $O(1)$ |
| 属性 get（集合） | $O(1)$ 均摊（`EnsureSubscribed` 幂等） |
| 属性 set（集合替换） | $O(k)$，$k$ = 旧 + 新条目数 |
| `CollectionChanged` 处理器 | $O(m)$，$m$ = 受影响条目数 |
| `ExecuteAsync`（容量空闲） | $O(1)$ |
| `ExecuteAsync`（排队） | $O(1)$ 入队，$O(n)$ 排队 |
| `Notify()` / `CanExecuteChanged` | $O(H)$ 处理器 |
| `Lock` / `UnLock` / `ChangeSemaphore` | $O(1)$ |
| `Interrupt` / `Clear` | $O(a + q)$ 活动 + 排队待取消调用 |
