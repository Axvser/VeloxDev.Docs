# MVVM — `ObservableCollectionTracker`

`VeloxDev.MVVM.ObservableCollectionTracker`（`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`）是一个 `static` 辅助类，由生成代码调用，使得集合属性的后备字段被直接初始化（例如 `= []`、绕过生成的 setter）时，`INotifyCollectionChanged.CollectionChanged` 订阅依然存在。

## Class: `ObservableCollectionTracker`

**Signature**

```csharp
public static class ObservableCollectionTracker
{
    public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler);
    public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler);
}
```

`NotifyCollectionChangedEventHandler` 即 `System.Collections.Specialized.NotifyCollectionChangedEventHandler`。

##### Methods

###### `ObservableCollectionTracker.EnsureSubscribed`

**Signature:**
`void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `collection` | `object?` | 要观察的集合。`null` 或未实现 `INotifyCollectionChanged` 时被忽略。 |
| `handler` | `NotifyCollectionChangedEventHandler` | 要挂上的处理器。重复挂上相同的 `(Method, Target)` 是空操作。 |

**Returns:** `void`。

**Exceptions:** 无。无法通知的 `collection` 是空操作而非错误。

**Example:**

```csharp
// Source: Generated — the getter of a [VeloxProperty] collection member
public ObservableCollection<string> Items
{
    get
    {
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
        return this._items;
    }
}
```

**Notes:**

- 由生成的属性 **getter** 在每次访问时调用；后续调用是快速的 O(1) 查找。
- 去重键是 `(Method, Target)` 身份，而非委托引用身份。生成的 getter 传的是 method group（`OnItemsCollectionChanged`），它每次访问都会产生**全新的**委托实例；按引用比较会导致每次读取都重复订阅，让事件的调用列表无界增长。
- 追踪存放在以集合身份为键的 `ConditionalWeakTable<object, Entry>` 中：集合被垃圾回收时条目一并消失 —— 不泄漏。该表对并发的 getter / setter 访问是安全的。

###### `ObservableCollectionTracker.Unsubscribe`

**Signature:**
`void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `collection` | `object?` | 要从中解绑的集合。`null` 或未实现 `INotifyCollectionChanged` 时被忽略。 |
| `handler` | `NotifyCollectionChangedEventHandler` | 要解绑的处理器。 |

**Returns:** `void`。

**Exceptions:** 无。

**Notes:**

- 由生成的属性 **setter** 在集合被替换时调用（`global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);`）。
- 它移除的是**订阅**，而不是订阅的记录：条目仍在，因此之后用同一处理器调用 `EnsureSubscribed` 会再次订阅该集合。这正是生成的 getter 所依赖的行为 —— 它每次读取都会调用 `EnsureSubscribed`。

## 为什么存在

像

```csharp
[VeloxProperty] private ObservableCollection<string> _items = [];
```

这样的成员通过初始化器 `= []` 给后备字段赋值，绕过了生成的 setter。如果订阅只发生在 setter 里，`CollectionChanged` 就永远观察不到。生成的 getter 改为调用 `EnsureSubscribed`，于是首次读取就订阅了私有的 `On{属性}CollectionChanged` 处理器。

## 由测试钉住的行为

`Src/Core/VeloxDev.Core.Test/MVVM/ObservableCollectionTrackerTests.cs`：

| 测试 | 契约 |
|---|---|
| `EnsureSubscribed_WithAFreshMethodGroupDelegate_SubscribesOnlyOnce` | 新委托、同方法同目标 → 只订阅一次 |
| `EnsureSubscribed_ReportsEachChangeExactlyOnce` | 一次变更 → 一次回调 |
| `Unsubscribe_DetachesTheHandler` | 解绑的处理器不再收到通知 |
| `Unsubscribe_ThenEnsureSubscribed_SubscribesAgain` | 条目仍在，因此可以重新订阅 |
| `EnsureSubscribed_TreatsDistinctTargetsAsDistinctHandlers` | 同一方法绑定到不同实例算不同处理器 |
| `EnsureSubscribed_OnSomethingThatCannotNotify_IsANoOp` | 非 `INotifyCollectionChanged` 的集合 |
| `Unsubscribe_OnACollectionNeverSubscribed_IsANoOp` | 解绑未知处理器 |
| `ConcurrentEnsureSubscribed_SubscribesOnce` | 并发读取 getter 仍然只订阅一次 |
