# 弱引用类型 — API 参考

命名空间 `VeloxDev.WeakTypes`（`VeloxDev.Core` 包）提供四个 sealed、泛型、线程安全的容器，它们以**弱引用**持有内容，因此长寿命的所有者 —— 事件发布者、任务积压队列、历史栈、缓存 —— 不会让它引用的对象常驻内存。

四个类型都有证据背书：源码位于 `Src/Core/VeloxDev.Core/WeakTypes/`，行为由 MSTest 测试套件（`Src/Core/VeloxDev.Core.Test/WeakTypes/`）钉死。

| 容器 | 弱引用模型 | 页面 |
|---|---|---|
| `WeakDelegate<TDelegate>` | 处理器存为 `WeakReference<Delegate>`；缓存组合委托让调用路径无锁 | [WeakDelegate](00_WeakDelegate/index.md) |
| `WeakQueue<T>` | 条目由 `Queue<WeakReference<T>>` 持有 —— FIFO | [WeakQueue](01_WeakQueue/index.md) |
| `WeakStack<T>` | 条目由 `Stack<WeakReference<T>>` 持有 —— LIFO | [WeakStack](02_WeakStack/index.md) |
| `WeakCache<TTargetKey,TCacheKey>` | 值绑定到弱键（经 `ConditionalWeakTable`）—— 条目随键一起消亡 | [WeakCache](03_WeakCache/index.md) |

## 命名空间与约束

- 四个类型都声明在单一命名空间 `VeloxDev.WeakTypes` 中，随 `VeloxDev.Core` 包分发。
- 类型参数在类级受约束：`WeakQueue<T>` 与 `WeakStack<T>` 要求 `where T : class`；`WeakDelegate<TDelegate>` 要求 `where TDelegate : Delegate`；`WeakCache<TTargetKey,TCacheKey>` 的两个参数都要求 `class`。
- 每个类型内部都加锁：变更、计数与枚举都取内部 `lock`。

## 如何选择容器

- 一对多发布，且订阅者生命周期不该被保活 → `WeakDelegate`（弱多播处理器集合）。
- 生产者/消费者积压，且队列里的任务不该被保活 → `WeakQueue`。
- 后进先出的历史记录，且最近的帧不该被保活 → `WeakStack`。
- 把缓存数据附加到瞬时目标，又不 root 住目标 → `WeakCache`。
