# 弱引用类型 — WeakDelegate<TDelegate>

`WeakDelegate<TDelegate>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs`）是一个类似事件、支持多个处理器的汇，其处理器列表以 `WeakReference<Delegate>` 条目代替强委托引用。当发布者比许多短命订阅者活得久、而你希望*列表*不要再把已死订阅者保活时使用它 —— 它对应着强 C# 事件的另一面：强事件里，发布者的委托链会把每个订阅者钉住。

泛型实参必须派生自 `System.Delegate`（例如 `WeakDelegate<Action<string>>`）。

## 1. 订阅并调用

`AddHandler` 把一个处理器作为弱引用追加；`Invoke(object?[] objects)` 通过 `DynamicInvoke` 触发当前的组合委托：

```csharp
using System;
using VeloxDev.WeakTypes;

var counter = new Counter();                // 辅助类定义在“完整代码”页
var subscriber = new Subscriber(counter);
var changed = new WeakDelegate<Action<string>>();

changed.AddHandler(subscriber.Handle);      // 存为 WeakReference<Delegate>
changed.Invoke(["hello"]);                  // object?[] 实参 -> DynamicInvoke
Console.WriteLine($"counter: {counter.Value}");   // 1
```

**预期结果：** 处理器恰好被调用一次（`counter.Value == 1`），对应 `WeakDelegateTests.cs` 里的单元测试 `AddHandler_And_Invoke_CallsHandler`（那里用 `Action<int>` 与 `Invoke([42])`）。`AddHandler(null)` 是空操作，对应 `AddHandler_Null_NoException`。

## 2. 移除处理器

`RemoveHandler` 从后往前扫描，把目标等于该处理器的每个条目移出列表，然后重建缓存：

```csharp
changed.AddHandler(subscriber.Handle);
changed.RemoveHandler(subscriber.Handle);   // 匹配条目从弱列表移除
changed.Invoke(["nobody"]);
Console.WriteLine($"counter: {counter.Value}");   // 仍为 1
```

**预期结果：** 移除后调用不再触发处理器，对应 `RemoveHandler_RemovesFromHandlerList`。

## 3. 已缓存的组合委托（依赖 GC 前请先读这段）

为了在热路径上避免加锁与反射，类型保存一个*已缓存的组合委托*（`_combinedDelegate`，`volatile` 字段）。`GetInvocationList()` 在缓存已建时直接返回它（无锁），仅在缓存为空时才重建：

```csharp
var typed = changed.GetInvocationList();    // TDelegate? = Action<string>?
typed?.Invoke("hello");                     // 类型化、无反射的调用
```

缓存是强组合委托，由此产生两点后果：

- `AddHandler` / `RemoveHandler` 带 `bool CanUpdateCache = true` 参数。默认值为 true 时会立即重建缓存，**每个并入缓存的存活处理器都会因缓存而变得强可达**。
- 以 `CanUpdateCache: false` 添加的处理器只会写进弱列表，*不会*并入缓存。它们保持可回收，因此在下一次重建前死去的订阅者会被 GC 丢弃。

这就是“完整代码”页里死处理器技巧要传 `CanUpdateCache: false` 的原因：

```csharp
var deadSub = new Subscriber(counter);
changed.AddHandler(deadSub.Handle, CanUpdateCache: false);   // 不入缓存，以便被回收
```

缓存只在下列时刻重建：以 `CanUpdateCache: true` 调用 `AddHandler` / `RemoveHandler`、`GetInvocationList()` 发现缓存为空、或 `Clone()` 内部。因此，想要确定性的退订请总是调用 `RemoveHandler`；想“让死订阅者自动掉落”，就以 `CanUpdateCache: false` 添加它们，并让之后的重建（或 `Clone`）去剪除。

**预期结果：** 同一个处理器添加两次后调用会触发两次；用 `CanUpdateCache: false` 添加第三个处理器，在下一次重建之前不会改变 `GetInvocationList()` 的返回值。

## 4. 用 Clone 做快照

`Clone()` 返回一个*新的* `WeakDelegate<TDelegate>`，只从当前存活的弱条目重建，且其缓存已就绪 —— 已被回收的订阅者自然缺席：

```csharp
var snapshot = changed.Clone();             // 只从存活处理器重建
snapshot.Invoke(["second"]);
```

**预期结果：** 已回收订阅者的处理器不会经克隆被调用。这对应测试 `Clone_ReturnsIndependentCopy` 与 `MultipleHandlers_CloneInvokesAll`（后者触发 `h1` 与 `h2`，并断言组合计数为 `11`）。
