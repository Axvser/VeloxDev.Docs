# MVVM — `ObservableCollectionTracker`

`VeloxDev.MVVM.ObservableCollectionTracker`（`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`）是一个 `static` 辅助类，供生成代码在集合属性的后备字段被直接赋值时，仍能保持 `INotifyCollectionChanged` 订阅。

**签名**

```csharp
public static void EnsureSubscribed(
    object? collection,
    NotifyCollectionChangedEventHandler handler)

public static void Unsubscribe(
    object? collection,
    NotifyCollectionChangedEventHandler handler)
```

- `EnsureSubscribed` — 若 `collection` 是 `INotifyCollectionChanged` 且尚未为 `handler` 订阅，则完成订阅。后续调用是 O(1) 的快速查找。由生成的属性 getter 在每次访问时调用。
- `Unsubscribe` — 从 `collection` 移除 `handler` 并删除追踪条目，避免订阅日后被意外恢复。由生成 setter 在集合被替换时调用。

## 为什么需要它

像下面这样的 `[VeloxProperty]` 集合成员通过初始化器 `= []` 直接给后备字段赋值，绕过了生成的 setter：

```csharp
[VeloxProperty] private ObservableCollection<string> _items = [];
```

如果只在 setter 里订阅，`CollectionChanged` 将永远不会被观察到。因此生成的 getter 会调用 `EnsureSubscribed`（见 `Base/Analizer.cs`，`MVVMPropertyFactory.GenerateGetter`），让首次读取完成对私有 `On{Property}CollectionChanged` 处理器的订阅，之后的每次读取都是无操作：

```csharp
get
{
    global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(_items, OnItemsCollectionChanged);
    return _items;
}
```

## 追踪模型

- 订阅记录在以集合身份为键的 `ConditionalWeakTable<object, Entry>` 中：集合被回收时其条目随之消失，因此没有泄漏。该表对并发的 getter/setter 访问是安全的。
- 处理器按 `(Method, Target)` 身份去重（`MethodTargetEqualityComparer`），而非按委托引用。生成的 getter 传入方法组（例如 `OnItemsCollectionChanged`），每次访问都会产生全新的委托实例；若按引用比较，就会在每次 getter 读取时重复订阅，让事件调用列表无界增长。

该追踪器所支撑的集合钩子（`OnCollectionChanged<T>`、`OnItemAddedTo{Property}`、`OnItemRemovedFrom{Property}`、`OnItemMovedIn{Property}`、`OnItemsResetIn{Property}`）由 MVVM 生成器产出——见 [00_VeloxPropertyAttribute](../00_VeloxPropertyAttribute/index.md)。
