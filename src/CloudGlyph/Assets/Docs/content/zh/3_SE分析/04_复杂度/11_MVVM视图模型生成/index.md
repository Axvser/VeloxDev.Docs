# MVVM视图模型生成

生成器本身没有运行时开销：它在编译期增量地发出普通 C# partial 成员，只有变更的类型会重新生成。运行时重要的是发出代码的形态——属性 setter 是常数时间加订阅者扇出，命令流水线带队列，集合钩子每次事件把项复制进数组。

记号：$s$ 个事件订阅者，一次变更 $k$ 个集合项，$p$ 个待处理命令，$a$ 个活跃命令，每类型 $M$ 个成员。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| 生成 | $O(\text{类型} \times M)$，编译期，增量 | 仅编译期 | `Src/Generators/VeloxDev.Core.Generator/MVVM.cs:16` |
| 生成的属性 set | $O(1) + O(s)$ | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:546` |
| 生成的属性 get（集合） | $O(1)$ 跟踪器查找 | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:701` |
| 集合变更派发 | 每事件 $O(k)$ | $O(k)$ 数组 | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:852` |
| 集合替换 | $O(k)$ | $O(k)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:741` |
| 注册集合处理器 | 均摊 $O(1)$ | 每对 $O(1)$ | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs:24` |
| 命令首次访问 | $O(1)$ 惰性构造 | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs:653` |
| 命令接受 / 入队 | $O(1) + O(s)$ | 每次执行 $O(1)$ | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:573` |
| 命令完成 + 排空 | 最坏 $O(k s)$ | $O(p)$ 待处理 | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:702` |
| `Interrupt` / `Clear` | $O(a s)$ / $O((a+p)s)$ | $O(a+p)$ | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:762` |

## 一次属性 set 是常数加扇出

默认 setter 先比较、保存旧值、调用两个变更钩子、赋值，再触发 `PropertyChanged`：

```csharp
if (global::System.Object.Equals(field, value)) return;
var old = field;
OnPropertyChanging(nameof(P));
OnXxxChanging(old, value);
field = value;
OnXxxChanged(old, value);
OnPropertyChanged(nameof(P));
```

出处：`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:554-564`

`partial void` 钩子未实现时被编译器擦除，`PropertyChanged?.Invoke` 在无订阅者时不分配。因此稳态代价为：

$$
T_{\text{set}} = O(1) + O(s) + T_{\text{Equals}}
$$

$T_{\text{Equals}}$ 是否装箱取决于类型：生成的调用使用 `Object.Equals(object, object)`，所以值类型属性会装箱两个操作数。这是*推断*的常数因子，不是渐近项。

## 集合事件先复制再派发

生成的集合处理器先构建旧项与新项数组，调用基类虚钩子，再按动作分支：

```csharp
switch (e.Action)
{
    case NotifyCollectionChangedAction.Add:
        ...
        OnItemAddedToItems(e.NewItems.Cast<T>().ToArray());
        break;
```

出处：`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:857-881`

每个钩子调用会再次把项枚举进另一个数组，所以一次 `Add` 约 $2k$ 次工作，一次 `Replace`（旧加新）约 $4k$。订阅本身是以集合为键的弱表，使用 `(method, target)` 比较器，避免重复安装同一处理器。

## 命令执行是队列，不是无锁调用

被接受的执行只取一次状态锁，加入活跃集或待处理队列，随后在启动主体前释放：

```csharp
await _stateLock.WaitAsync();
...
if (_active.Count < maxConcurrency) { _active.Add(item); accepted = true; }
else { _pendingQueue.Enqueue(item); }
...
_stateLock.Release();
...
_ = ExecuteCoreAsync(item);
```

出处：`Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:589-631`

完成时以 $O(1)$ 从活跃集移除，并在容量允许时排空待处理项：

```csharp
while (pending > 0 && active < maxConcurrency && !_isForceLocked)
{
    ...
}
```

出处：`Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:926-933`

每个被排空的项都会触发事件，所以一次完成若启动 $k$ 个排队命令，在 $s$ 个订阅者下花费 $O(k s)$。没有订阅者时，事件触发器在分配副本前就返回。

```plot
{
  "title": "命令完成时的排空",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(k) 次状态迁移" },
    { "fn": "4*x", "color": "#f472b6", "title": "4 个订阅者时 O(k*s)" }
  ]
}
```

## 内存

一个生成的命令是一个惰性字段加信号量、队列、哈希集和十六个委托槽——每个命令实例恒定。正在执行的命令花费 $O(p)$ 个待处理项与 $O(a)$ 个活跃项，每项一个事件参数对象与可选取消源。带类型参数的命令在 `ConcurrentDictionary` 中每类型保存一个命令，所以每实例代价是 $O(T)$，$T$ 为用到的参数类型数。
