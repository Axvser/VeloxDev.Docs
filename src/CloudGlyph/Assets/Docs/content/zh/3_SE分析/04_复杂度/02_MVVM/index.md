# 复杂度分析 — MVVM

所有界都针对 `Src/Core/VeloxDev.Core/MVVM/{CommandPipeline{TParam,TResult}.cs, CommandCompletion.cs, ObservableCollectionTracker.cs}` 中的运行时，以及 `Src/Generators/VeloxDev.Core.Generator/{Base/Analizer.cs, Writers/CommandWriter.cs}` 中的生成模板。源生成器在编译期为每个被标注类型增加 $O(P + C)$ 个生成成员，其中 $P$ 是 `[VeloxProperty]` 成员数，$C$ 是 `[VeloxCommand]` 方法数；这些工作不会在运行期重复。

**记号。** $n$ = 在途执行数（活动 + 排队），$k$ = 集合替换时旧 + 新集合的项数，$m$ = 一次 `CollectionChanged` 影响的项数，$H$ = 单个事件的订阅者数，$R$ = 想为一次执行上报 `Canceled` 的发射者数。

## 生成的属性 setter（默认模式）

$$
T_{\text{set}}(scalar) = O(1)
$$

步骤是相等性守卫、捕获 `old`、`OnPropertyChanging`、`On{Name}Changing`、赋值、`On{Name}Changed` 与 `OnPropertyChanged`。setter 体由 `MVVMPropertyFactory.GetSetterBodyLines`（`Base/Analizer.cs`）产出。

```csharp
// Source: Base/Analizer.cs —— Default setter 模式
if(global::System.Object.Equals(this._count, value)) return;
var old = this._count;
OnPropertyChanging(nameof(Count));
OnCountChanging(old, value);
this._count = value;
OnCountChanged(old, value);
OnPropertyChanged(nameof(Count));
```

对实现 `INotifyCollectionChanged` 的属性，替换集合还会调用 `Unsubscribe(old, …)`、`EnsureSubscribed(value, …)`，并对被替换集合的项调用 `OnItemRemovedFrom{Name}` / `OnItemAddedTo{Name}`：

$$
T_{\text{set}}(collection\ replacement) = O(k), \qquad k = |\text{old}| + |\text{new}|
$$

非替换的 getter 路径保持常数，外加摊还的 tracker 查找：

$$
T_{\text{get}}(collection) = O(1)\ \text{amortized}
$$

## 属性变更扇出

$$
T_{\text{notify}}(scalar) = O(1) + O(H)
$$

其中 $H$ 是订阅了 `PropertyChanged` / `PropertyChanging` 的处理器数。扇出由订阅者主导，而非属性数量。

## CollectionChanged 处理器（每次变更）

生成的 `On{Name}CollectionChanged` 把原始事件转发给 `OnCollectionChanged<T>`；在 Add / Remove / Replace / Move 时通过 `Enumerate{Name}Items` → `ToArray` 物化受影响的项：

$$
T_{\text{mutation}} = O(m)
$$

$m$ 为受影响项数（`MVVMPropertyFactory.GenerateCollectionMembers`）。`Reset` 是 $O(1)$：它不携带项，直接分发到 `OnItemsResetIn{Name}`。

## `ObservableCollectionTracker`

$$
\text{EnsureSubscribed} = O(1)\ \text{amortized}, \qquad \text{Unsubscribe} = O(1)
$$

`ConditionalWeakTable.GetOrCreateValue` 加一次 `HashSet<Delegate>` 添加（由锁保护）。去重键是处理器的 `(Method, Target)` 对，这使重复 getter 访问保持幂等：

$$
q \text{ 次 getter 读取} \;\Rightarrow\; 1 \text{ 次订阅}
$$

没有该去重，事件的调用列表会每次读取增长一个委托，之后一次变更的代价会变成 $O(q)$ 而不是 $O(1)$。

弱引用键意味着集合被回收时追踪条目消失，因此表的大小以存活集合为界。

## 命令执行

容量可用时的普通执行：

$$
T_{\text{execute}} = O(1)
$$

`ExecuteCore` 做一次 `SemaphoreSlim.WaitAsync`、一次 `_active.Add` 并启动方法体。容量耗尽时入队：

$$
T_{\text{enqueue}} = O(1), \qquad \text{queue depth} \le n
$$

`TryStartPendingAsync` 一次最多排空 `_maxConcurrency` 个项：

$$
T_{\text{drain}} = O(n)\ \text{for the drain}, \qquad O(1)\ \text{amortized per trigger}
$$

`CanExecute` 以 $O(1)$ 计算用户谓词与强制锁标志；`Notify()` → `RaiseCanExecuteChanged()` 是 $O(H)$（`CanExecuteChanged` 订阅者数）。

`EventContext` 改变常数而非复杂度：设置上下文后，每个事件多一次 `SynchronizationContext.Post`（$O(1)$），但处理器在上下文线程上按自己的时机运行。

强类型命令让形参与结果以自身类型穿过队列，因此每次执行仍是 $O(1)$，只是装箱更少；arity 族把多形参打包进 `ValueTuple`，它是结构体，不分配。

## 取消、清空与释放

$$
T_{\text{interrupt}} = O(a), \qquad T_{\text{clear}} = O(a + q)
$$

其中 $a$ = 活动执行数，$q$ = 排队执行数（`InterruptAsync`、`ClearAsync`）。两者都对受影响项数线性，因为每个项需要一次 `Cancel()` 与一次事件。

每次执行的资源处理是 $O(1)$：`_isCtsNeeded` 为真时创建一个 `CancellationTokenSource`，并恰好释放一次 —— 跑过的执行由 `ExecuteCoreAsync` 的 `finally` 释放，从未运行的排队项由 `ClearAsync` 释放。`TakeCts` 是 `Interlocked.Exchange`，$O(1)$，因此两个竞争者不可能同时认领释放责任。

## 可等待路径

$$
T_{\text{executeAndWait}} = T_{\text{execute}} + O(1)
$$

`ExecuteAndWaitAsync` 在 `ExecuteAsync` 之上增加一个 `TaskCompletionSource<CommandCompletion>` 与一次 token 注册。完成 sink 是 $O(1)$（`TrySetResult` / `TrySetCanceled`），`RunContinuationsAsynchronously` 让续体不落在管线栈上。`ExecuteAndWaitTypedAsync` 形状相同，只是完成类型是强类型的；返回 `TResult` 免去未强类型路径的装箱。

单条 `Canceled` 保证是 $O(1)$：

$$
\text{reports per execution} = \min(R,\ 1) = 1
$$

`TryMarkCancelReported` 是一次 `Interlocked.Exchange`，因此无论多少发射者（`Interrupt`、`Clear`、方法体自己的 `OperationCanceledException`）想上报取消，只有第一个成功。

## 内存占用

| 结构 | 复杂度 |
| --- | --- |
| 每个被标注类型的生成成员 | $O(P + C)$，每类型常数 |
| 命令状态 | $O(n)$ 个 `CommandEventArgs`，分布在 `_active`（`HashSet`）与 `_pendingQueue`（`Queue`） |
| 每次执行、已订阅阶段 | **每个有订阅者的阶段**一个 $O(1)$ `CommandEventArgs`；无订阅者的阶段不分配 |
| 每次执行、等待调用 | $O(1)$：一个 `TaskCompletionSource` |
| 每次可取消执行 | $O(1)$：一个 `CancellationTokenSource`，在该执行结束时释放 |
| `ObservableCollectionTracker` 表 | $O(\text{存活集合数})$，通过 `ConditionalWeakTable` |
| `CommandCompletion` | `readonly struct`：自身不分配 |
| 强类型命令的实参/结果 | 强类型路径不装箱；经 `ICommand` 绑定仍会装箱 |

按订阅者分配的规则是代码刻意围绕其塑造的界：

$$
\text{alloc} = O\bigl(|\{\text{至少有一个订阅者的阶段}\}|\bigr)
$$

`CommandAllocationTests` 以相对方式钉住它 —— 无订阅者的命令每次执行的分配必须严格少于订阅全部八个事件的命令 —— 而不是与绝对值比较，这样运行时改形状时断言不会过期。

## 逐操作汇总

| 操作 | 复杂度 |
| --- | --- |
| 属性 get（非集合） | $O(1)$ |
| 属性 get（集合） | $O(1)$ 摊还（`EnsureSubscribed` 幂等） |
| 属性 set（非集合） | $O(1) + O(H)$ 订阅者扇出 |
| 属性 set（集合替换） | $O(k)$，$k$ = 旧 + 新项数 |
| `CollectionChanged` 处理器 | $O(m)$，$m$ = 受影响项数（`Reset` 为 $O(1)$） |
| `ObservableCollectionTracker.EnsureSubscribed` | $O(1)$ 摊还 |
| `ObservableCollectionTracker.Unsubscribe` | $O(1)$ |
| `CanExecute` | $O(1)$ |
| `Execute` / `ExecuteAsync`（有空闲容量） | $O(1)$ |
| `ExecuteAsync`（排队） | 入队 $O(1)$；排空时每次触发摊还 $O(1)$ |
| `ExecuteAndWaitAsync` / 强类型版本 | 同 `ExecuteAsync` $+ O(1)$ |
| `IsBusy` / `ActiveCount` / `PendingCount` | $O(1)$ —— 两次 `Count` 读取，不取锁 |
| 扩展方法查找 | $O(1)$：一次 `as` 转换，或抛 `NotSupportedException` |
| `Notify()` / `CanExecuteChanged` | $O(H)$ 个处理器 |
| `Lock` / `Unlock` / `Continue` | $O(1)$，队列非空时再加一次排空 |
| `ChangeSemaphore` | $O(1) + O(n)$ 排空 |
| `Interrupt` | $O(a)$ |
| `Clear` | $O(a + q)$ |
| `Dispose` | $O(1)$ |

## 关于这些界的说明

- 全部是**稳态**成本。生成器的工作在编译期，不出现在运行期。
- $H$、$n$、$a$、$q$、$k$、$m$ 从库的角度无界；这些界在这些参数上是精确的。
- `EventContext` 路径用顺序保证换线程亲和性，而不是换时间：复杂度不变，但事件异步投递。
- `IsBusy` / `ActiveCount` / `PendingCount` 刻意**不同步**于状态锁，因此并发更新可能让值落后一步。读取是 $O(1)$ 但非线性化 —— 这是刻意的取舍。
