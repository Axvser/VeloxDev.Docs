# 弱引用类型 — 选择容器

四种类型解决不同的泄漏/生命周期问题。先用下表选择，再跳到对应页面。

## 1. 场景表

| 场景 | 类型 | 原因 |
|---|---|---|
| 类事件的发布者，不能让死掉的订阅者被保活（“弱事件”） | `WeakDelegate<TDelegate>` | 每个处理器以 `WeakReference<Delegate>` 存储。并入强组合缓存的处理器在下次重建前一直被保活；需要真正可回收的订阅时以 `CanUpdateCache: false` 添加。 |
| 不能钉住生产者对象的 FIFO 缓冲——只在生产对象仍存活时处理工作项 | `WeakQueue<T>` | 条目是 `WeakReference<T>`；唯一引用只剩队列的条目会被回收，访问时跳过并剪除死条目。 |
| 不能保活其所有者的短命状态的 LIFO（撤销/重做、返回栈） | `WeakStack<T>` | 与队列相同的弱条目模型，LIFO 顺序。 |
| 目标键消失后值也应消失的按目标存放值（临时侧表） | `WeakCache<TTargetKey, TCacheKey>` | 基于 `ConditionalWeakTable<TTargetKey, TCacheKey>`，它不会 root 键。 |

**预期结果：** 对每一行，你能在阅读详细页之前说出确切的泛型类型——包括它的类型参数。

## 2. 共同约束

泛型约束直接来自 `Src/Core/VeloxDev.Core/WeakTypes/` 的源码签名：

- `WeakDelegate<TDelegate>` 要求 `where TDelegate : Delegate` —— 处理器是委托实例。
- `WeakQueue<T>` 与 `WeakStack<T>` 要求 `where T : class` —— 条目必须是引用类型。
- `WeakCache<TTargetKey, TCacheKey>` 要求 `where TTargetKey : class` **且** `where TCacheKey : class` —— 键和值都是引用类型。

值类型（例如 `int`、`struct`）会在编译期被拒绝，因为 `WeakReference<T>` 只能跟踪引用类型目标。若需要弱槽位存值，用一个小的类包一层，或按自己的生命周期规则使用可空字段。

**预期结果：** 编译器接受 `WeakQueue<SomeClass>`，并以约束错误拒绝 `WeakQueue<int>`。

## 3. 什么时候不要用弱集合

- **你需要条目在集合存活期间一直存活。** 弱集合不是保证——若某条目的唯一引用是弱引用，GC 可以回收它。正确性要求条目必须存在时（一个之后真要取干的真实工作队列），请在别处保留强引用。
- **你已掌控生命周期。** 如果订阅者/所有者与事件源的生命周期明确且有界，显式退订（或从集合移除）比重依赖 GC 更便宜、更可预测。
- **你需要跨 GC 的 `IEnumerable` 顺序保证。** 枚举会先剪除且只产出存活条目，因此两次枚举之间若发生 GC，可见内容可能变化。
- **键/值是驻留字符串或静态字符串。** 字符串字面量会被运行时 root 住整个进程，因此用字面量构建的 `WeakCache<string, string>`（某些单测正是如此）永远不会真正驱逐。想观察驱逐，请使用真实对象实例。

**预期结果：** 对每个“不要”场景，你能说出自己*不会*选哪个类型以及原因。
