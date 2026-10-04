# 复杂度分析 — MVVM

所有界均针对 `Src/Core/VeloxDev.Core/MVVM/{VeloxCommand.cs, CommandCompletion.cs, ObservableCollectionTracker.cs}` 中的运行时，以及 `Src/Generators/VeloxDev.Core.Generator/{Base/Analizer.cs, Writers/CommandWriter.cs}` 中的生成代码模板。源生成器自身在编译期为每个被标注类型增加 $O(P + C)$ 个生成成员，其中 $P$ 是 `[VeloxProperty]` 字段/partial 属性的数量，$C$ 是 `[VeloxCommand]` 方法的数量；这些工作在运行期完全不重复。

**记号。** $n$ = 在途执行数（活动 + 排队），$k$ = 替换期间旧 + 新集合的条目数，$m$ = 一次 `CollectionChanged` 影响的条目数，$H$ = 单个事件的订阅者数，$R$ = 想为同一次执行上报 `Canceled` 的发出者数。

## 生成的属性 setter（默认模式）

无论值类型如何，生成的 setter 都执行常数次操作：

$$
T_{\text{set}}(scalar) = O(1)
$$

步骤为 `Object.Equals` 守卫、捕获 `old`、`OnPropertyChanging`、`On{名称}Changing`、字段赋值、`On{名称}Changed` 与 `OnPropertyChanged` —— 全部常数时间。setter 体由 `MVVMPropertyFactory.GetSetterBodyLines` 产出（`Base/Analizer.cs` 第 466 行），并在生成文件中得到确认：

```csharp
// Source: Generated — CounterViewModel_QuickStart_Mvvm_MVVM.g.cs, the Count property
if (global::System.Object.Equals(this._count, value)) return;
var old = this._count;
OnPropertyChanging(nameof(Count));
OnCountChanging(old, value);
this._count = value;
OnCountChanged(old, value);
OnPropertyChanged(nameof(Count));
```

对于 `INotifyCollectionChanged` 属性，替换整个集合还会调用 `Unsubscribe(old, …)` 与 `EnsureSubscribed(value, …)`，并针对被替换集合的条目调用 `OnItemRemovedFrom{名称}` / `OnItemAddedTo{名称}`：

$$
T_{\text{set}}(collection\ replacement) = O(k), \qquad k = |\text{old}| + |\text{new}|
$$

非替换的 getter 路径保持常数，外加摊还的 tracker 查找：

$$
T_{\text{get}}(collection) = O(1)\ \text{amortized}
$$

## 属性变更扇出

设置一个属性会触发 partial 钩子以及通知事件，后者扇出到每个订阅者：

$$
T_{\text{notify}}(scalar) = O(1) + O(H)
$$

其中 $H$ 是已订阅的 `PropertyChanged` / `PropertyChanging` 处理器数（通常是一两个绑定）。扇出由订阅者主导，而不是由属性数量主导。

## CollectionChanged 处理器（每次变更）

生成的 `On{名称}CollectionChanged` 以常数时间把原始事件转发给 `OnCollectionChanged<T>`，并在 Add / Remove / Replace / Move 时经 `Enumerate{名称}Items` → `ToArray` 物化受影响的条目：

$$
T_{\text{mutation}} = O(m)
$$

$m$ 为受影响的条目数（`MVVMPropertyFactory.GenerateCollectionMembers`，`Base/Analizer.cs` 第 754 行）。`Reset` 是 $O(1)$：它不携带条目，直接分派到 `OnItemsResetIn{名称}`。

## `ObservableCollectionTracker`

$$
\text{EnsureSubscribed} = O(1)\ \text{amortized}, \qquad \text{Unsubscribe} = O(1)
$$

`ConditionalWeakTable.GetOrCreateValue` 加上受锁保护的 `HashSet<Delegate>` 添加（`Entry.TryAdd`）。去重键是处理器的 `(Method, Target)` 对（`MethodTargetEqualityComparer`，`ObservableCollectionTracker.cs` 第 100-118 行），这正是让重复 getter 读取幂等的原因：

$$
q \text{ 次 getter 读取} \;\Rightarrow\; 1 \text{ 次订阅}
$$

值得点名的微妙之处：没有 `(Method, Target)` 去重时，读取的**时间**仍是 $O(q)$，但事件的调用列表会每次读取增长一个委托，于是之后单次变更的代价会变成 $O(q)$ 而不是 $O(1)$。比较器正是阻断这一点的那一环。

弱引用键意味着集合被垃圾回收时追踪条目一并消失 —— 不泄漏，因此表的规模由存活集合数界定，而不是由曾出现过的集合数界定。

## 命令执行

容量可用时的普通执行：

$$
T_{\text{execute}} = O(1)
$$

`ExecuteCore` 做一次 `SemaphoreSlim.WaitAsync` + `_active.Add` + 即发即忘（`VeloxCommand.cs` 第 474-531 行）。容量耗尽时条目入队：

$$
T_{\text{enqueue}} = O(1), \qquad \text{队列深度} \le n
$$

`TryStartPendingAsync`（第 794-822 行）一次最多排空 `_maxConcurrency` 个条目：

$$
T_{\text{drain}} = O(n)\ \text{for the drain}, \qquad O(1)\ \text{amortized per trigger}
$$

`CanExecute` 以 $O(1)$ 求用户谓词与强制锁标志（第 407-408 行），`Notify()` → `RaiseCanExecuteChanged()` 是 $O(H)$，$H$ 为 `CanExecuteChanged` 订阅者数。

`EventContext` 改变的是常数而非复杂度：设置上下文后每个事件多一次 `SynchronizationContext.Post` —— $O(1)$ —— 但处理器改为在上下文的线程上于它自己的时刻运行。

## 取消、清空与释放

$$
T_{\text{interrupt}} = O(a), \qquad T_{\text{clear}} = O(a + q)
$$

其中 $a$ = 活动、$q$ = 排队被清扫的执行数（`InterruptAsync` 第 642-683 行、`ClearAsync` 第 686-747 行）。两者对受影响条目数都是线性的，因为每一个都需要一次 `Cancel()` 与一个事件。

每次执行的资源处理是 $O(1)$：`_isCtsNeeded` 时创建一个 `CancellationTokenSource`，并恰好释放一次 —— 跑过的由 `ExecuteCoreAsync` 的 `finally` 负责（第 569-578 行），从未运行的排队项则由 `ClearAsync` 自己负责（第 715-723 行）。`TakeCts`（第 888 行）是 `Interlocked.Exchange`，$O(1)$，因此两个竞争者不可能同时取得释放权。

## 可等待路径

$$
T_{\text{executeAndWait}} = T_{\text{execute}} + O(1)
$$

相对 `ExecuteAsync`，`ExecuteAndWaitAsync`（第 452-471 行）只多了一个 `TaskCompletionSource<CommandCompletion>` 与一次 token 注册。收尾 sink 经 `TrySetResult` / `TrySetCanceled` 是 $O(1)$，而 `RunContinuationsAsynchronously` 让延续不落在管线的栈上。

单条 `Canceled` 的保证是 $O(1)$：

$$
\text{reports per execution} = \min(R,\ 1) = 1
$$

`TryMarkCancelReported` 是单次 `Interlocked.Exchange`（第 896 行），因此无论有多少发出者想上报取消 —— `Interrupt`、`Clear`、方法体自身的 `OperationCanceledException` —— 恰好第一个会成功。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 每个被标注类型的生成成员 | $O(P + C)$，每类型常数；$P$ = `[VeloxProperty]` 成员数，$C$ = `[VeloxCommand]` 方法数 |
| `VeloxCommand` 状态 | $O(n)$ 个 `CommandEventArgs`，分布于 `_active`（`HashSet`，第 198 行）+ `_pendingQueue`（`Queue`，第 196 行） |
| 每次执行、有订阅的阶段 | 每个**有订阅者的阶段** $O(1)$ 个 `CommandEventArgs`；没有订阅者的阶段不分配任何东西（`RaiseCommandEventAs`，第 373-393 行） |
| 每次执行、等待中的调用 | $O(1)$：一个 `TaskCompletionSource` |
| 每次可取消执行 | $O(1)$：一个 `CancellationTokenSource`，在该次执行结束时释放 |
| `ObservableCollectionTracker` 表 | $O(\text{存活集合数})$，经 `ConditionalWeakTable` —— 随集合一起被回收 |
| `CommandCompletion` | `readonly struct`：自身 $0$ 分配 |

按订阅者分配的规则值得单列成界，因为它正是代码刻意围绕其塑形的那一条：

$$
\text{alloc} = O\bigl(|\{\text{至少有一个订阅者的阶段}\}|\bigr)
$$

`CommandAllocationTests` 以**相对**方式钉住它 —— 无订阅者的命令每次执行的分配必须严格少于订阅了全部八个事件的命令 —— 而不是对照绝对数值，这样断言不会在运行时形态变化时失效。

## 逐操作汇总

| 操作 | 复杂度 |
|---|---|
| 属性读（非集合） | $O(1)$ |
| 属性读（集合） | $O(1)$ 摊还（`EnsureSubscribed` 幂等） |
| 属性写（非集合） | $O(1) + O(H)$ 订阅者扇出 |
| 属性写（集合替换） | $O(k)$，$k$ = 旧 + 新条目数 |
| `CollectionChanged` 处理器 | $O(m)$，$m$ = 受影响条目数（`Reset` 时 $O(1)$） |
| `ObservableCollectionTracker.EnsureSubscribed` | $O(1)$ 摊还 |
| `ObservableCollectionTracker.Unsubscribe` | $O(1)$ |
| `CanExecute` | $O(1)$ |
| `Execute` / `ExecuteAsync`（容量空闲） | $O(1)$ |
| `ExecuteAsync`（排队） | $O(1)$ 入队；被排空时每次触发摊还 $O(1)$ |
| `ExecuteAndWaitAsync` | 同 `ExecuteAsync` $+ O(1)$ |
| `IsBusy` / `ActiveCount` / `PendingCount` | $O(1)$ —— 两次 `Count` 读取，不取锁（第 269-283 行） |
| `ExecuteAndWaitAsync` / `IsBusy` 扩展查找 | $O(1)$：一次 `as` 转换，或抛 `NotSupportedException` |
| `Notify()` / `CanExecuteChanged` | $O(H)$ 个处理器 |
| `Lock` / `Unlock` / `Continue` | $O(1)$，队列非空时再加一次排空 |
| `ChangeSemaphore` | $O(1) + O(n)$ 排空 |
| `Interrupt` | $O(a)$ |
| `Clear` | $O(a + q)$ |
| `Dispose` | $O(1)$ |

## 这些界的适用前提

- 它们全是**稳态**成本。生成器自身的工作在编译期，运行期完全不出现。
- 从库的角度看 $H$、$n$、$a$、$q$、$k$、$m$ 都无上界：调用方可以订阅任意多个处理器或排入任意多次调用。这些界在这些参数上是精确的，而不是在某个固定常数上。
- `EventContext` 路径拿顺序保证换取线程亲和，而不是换取时间：复杂度不变，但事件是异步投递的，因此处理器可能在触发该事件的调用返回之后才观察到命令。
- `IsBusy` / `ActiveCount` / `PendingCount` 刻意**不**与状态锁同步，因此并发更新可能让它们滞后一步。读取它们是 $O(1)$ 但不可线性化 —— 这是记录在第 265-268 行的刻意取舍。

> 来源：`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`（`ExecuteCore` 474、`ExecuteCoreAsync` 533、`TryStartPendingAsync` 794、`InterruptAsync` 642、`ClearAsync` 686、`ExecuteAndWaitAsync` 452、`CanExecute` 407、`IsBusy` 269）、`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` 第 15-118 行、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory.GetSetterBodyLines` 466、`GenerateCollectionMembers` 754）、`Src/Core/VeloxDev.Core.Test/MVVM/CommandAllocationTests.cs`。
