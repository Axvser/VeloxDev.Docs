# 弱引用类型 — WeakCache<TTargetKey, TCacheKey>

`WeakCache<TTargetKey, TCacheKey>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs`）把一个**值**挂到某个**目标键**上，让这个值恰好和目标键活得一样久。它建立在 `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>` 之上 —— 该表从不把键保活：键一不可达，条目就随它一起被回收。两个类型实参都必须是引用类型。

把它想成一张“按对象”的旁表：为这个存活对象记住一个派生值（一次缓存的分析结果、一个标签、一个事件订阅计数），又不会让表变成永远把键保活的泄漏源。

## 1. 增、读、覆盖写

`AddOrUpdate(target, value)` 插入或替换关联；`TryGetCache(target, out value)` 读回（键存活且存在时返回 `true` 与值，否则返回 `false` 且 `out null`）：

```csharp
using System;
using VeloxDev.WeakTypes;

var cache = new WeakCache<Payload, string>();   // Payload 是“完整代码”页里的辅助类
var key1 = new Payload(100);

cache.AddOrUpdate(key1, "value-100");
if (cache.TryGetCache(key1, out var label)) Console.WriteLine($"label: {label}");   // value-100

cache.AddOrUpdate(key1, "updated");             // 覆盖关联
Console.WriteLine(cache.TryGetCache(key1, out var v2) ? v2 : "(null)");            // updated
```

**预期结果：** 不存在的关联返回 `false`（`TryGetCache_Missing_ReturnsFalse`），对同一键再次添加会替换旧值（`AddOrUpdate_OverwritesExisting`），对应 `WeakCacheTests.cs`。

## 2. 移除

`Remove(target)` 若存在则删除关联；移除一个未缓存的键是无害的空操作：

```csharp
cache.Remove(key1);
Console.WriteLine($"after Remove: {cache.TryGetCache(key1, out _)}");   // False
```

**预期结果：** `Remove` 后查找返回 `false`（`Remove_DeletesEntry`），而 `cache.Remove(new Payload(999))` 不抛异常（`Remove_NonExistent_NoException`）。

## 3. 枚举存活关联

`ForeachCache(Action<TTargetKey, TCacheKey> action)` 对每个*存活*的键值对调用你的回调：

```csharp
var second = new Payload(200);
cache.AddOrUpdate(key1, "value-100");
cache.AddOrUpdate(second, "value-200");
cache.ForeachCache((key, value) => Console.WriteLine($"key={key.Value} -> {value}"));
```

**预期结果：** 回调对每个存活条目执行一次 —— 对应 `ForeachCache_IteratesAllEntries`（该测试把访问过的键值对收进字典，并断言两者都在）。

## 4. 驱逐由键驱动

因为表不把键保活，驱逐发生在键自己的寿命上，而不是显式的大小上限：

- 当 `key1` 失去最后一个强引用且 GC 运行后，它的行会从条件弱表里消失，之后的 `TryGetCache(key1, out _)` 返回 `false`。
- 缓存还维护一个 `WeakReference<TTargetKey>` 簿记列表（用于廉价枚举键）；这些弱引用从不把键保活，过期条目在 `ForeachCache` 运行时、或当插入计数在 `AddOrUpdate` 内部越过某个清理阈值时被移除（`AddOrUpdate_ManyItems_TriggersCleanup` 用 20 个存活的 `object` 键演练这条路径）。
- 单元测试用的是被运行时驻留、永远不会被回收的*字符串字面量*键，因此它们证明的是 API 行为而非驱逐。[验证与完整代码](../08_验证与完整代码/)页那个可运行程序用真实的 `Payload` 键，展示 GC 回收死键后 `TryGetCache` 返回 `false`。

**预期结果：** 你能预测一次 GC 后哪些关联存活；也知道添加 20 个存活键后再读最后一个仍然成功。精确 GC 规则见[GC行为与注意](../07_GC行为与注意/)页。
