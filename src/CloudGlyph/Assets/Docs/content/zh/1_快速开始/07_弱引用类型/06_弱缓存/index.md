# 弱引用类型 — `WeakCache<TTargetKey, TCacheKey>`

`WeakCache<TTargetKey, TCacheKey>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs`）把一个**值**附加到一个**目标键**上，使值的寿命与键完全一致。它基于 `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>`，后者从不 root 键——键一旦不可达，条目就可以随它一起被回收。两个类型参数都必须是引用类型。

可以把它想成按对象存放的侧表：“对这个存活对象，记住这个派生值”（缓存的分析结果、标签、事件订阅计数），同时又不让表变成永久保活键的泄漏。

## 1. 添加、读取、覆盖

`AddOrUpdate(target, value)` 插入或替换关联；`TryGetCache(target, out value)` 读回（键存活且存在时返回 `true` 和值，否则返回 `false` 且 `out null`）：

```csharp
using System;
using VeloxDev.WeakTypes;

var cache = new WeakCache<Payload, string>();   // Payload is the helper from the Complete Code page
var key1 = new Payload(100);

cache.AddOrUpdate(key1, "value-100");
if (cache.TryGetCache(key1, out var label)) Console.WriteLine($"label: {label}");   // value-100

cache.AddOrUpdate(key1, "updated");             // overwrite the association
Console.WriteLine(cache.TryGetCache(key1, out var v2) ? v2 : "(null)");            // updated
```

**预期结果：** 缺失关联返回 `false`（`TryGetCache_Missing_ReturnsFalse`），重复添加同一个键会替换旧值（`AddOrUpdate_OverwritesExisting`），与 `WeakCacheTests.cs` 一致。

## 2. 移除

`Remove(target)` 删除存在的关联；移除未缓存的键是无害的无操作：

```csharp
cache.Remove(key1);
Console.WriteLine($"after Remove: {cache.TryGetCache(key1, out _)}");   // False
```

**预期结果：** `Remove` 之后查询返回 `false`（`Remove_DeletesEntry`），且 `cache.Remove(new Payload(999))` 不抛异常（`Remove_NonExistent_NoException`）。

## 3. 枚举存活关联

`ForeachCache(Action<TTargetKey, TCacheKey> action)` 对每个*存活*键/值对调用你的回调：

```csharp
var second = new Payload(200);
cache.AddOrUpdate(key1, "value-100");
cache.AddOrUpdate(second, "value-200");
cache.ForeachCache((key, value) => Console.WriteLine($"key={key.Value} -> {value}"));
```

**预期结果：** 回调对每个存活条目运行一次——对应 `ForeachCache_IteratesAllEntries`，它把访问到的键值对收进字典并断言两者都在。

## 4. 驱逐由键驱动

由于表不 root 其键，驱逐取决于键自身的寿命，而不是显式的大小上限：

- 当 `key1` 失去最后的强引用且 GC 运行后，它的行从条件弱表中消失，之后的 `TryGetCache(key1, out _)` 返回 `false`。
- 缓存还维护一个 `WeakReference<TTargetKey>` 的记账列表（用于低成本枚举键）；这些弱引用从不钉住键，陈旧条目会在 `ForeachCache` 运行时、`Remove` 命中已知键时，或插入计数器越过 `AddOrUpdate` 内部清理阈值时被移除（`AddOrUpdate_ManyItems_TriggersCleanup` 用 20 个存活的 `object` 键走过这条路径）。
- 单测使用*字符串字面量*键，它们被运行时驻留因此永不回收，所以测试证明的是 API 行为而非驱逐。验证与完整代码页的可运行程序使用真实 `Payload` 键，并展示 GC 移除死键后 `TryGetCache` 返回 `false`。

**预期结果：** 你能预测 GC 后哪些关联存活，并且知道添加 20 个存活键后读取最后一个仍然成功。详细 GC 规则见 GC 行为页。
