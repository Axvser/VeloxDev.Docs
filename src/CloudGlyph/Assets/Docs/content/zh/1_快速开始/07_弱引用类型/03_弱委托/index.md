# 弱引用类型 — `WeakDelegate<TDelegate>`

`WeakDelegate<TDelegate>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs`）是一个类事件的多处理器容器，其处理器列表持有 `WeakReference<Delegate>` 条目而不是强委托引用。当发布者的寿命长于大量短命订阅者，而你想让*列表*不再保活已死订阅者时使用它——它是强 C# `event` 的对应物，后者会让发布者的委托链钉住每个订阅者。

泛型参数必须派生自 `System.Delegate`（例如 `WeakDelegate<Action<string>>`）。

## 1. 订阅与调用

`AddHandler` 把处理器追加到弱列表；`Invoke(object?[] objects)` 通过 `DynamicInvoke` 触发当前组合委托：

```csharp
using System;
using VeloxDev.WeakTypes;

var counter = new Counter();                // helper classes from the Complete Code page
var subscriber = new Subscriber(counter);
var changed = new WeakDelegate<Action<string>>();

changed.AddHandler(subscriber.Handle);      // stored as WeakReference<Delegate>
changed.Invoke(["hello"]);                  // object?[] argument -> DynamicInvoke
Console.WriteLine($"counter: {counter.Value}");   // 1
```

**预期结果：** 处理器运行一次（`counter.Value == 1`），与 `WeakDelegateTests.cs` 中的单测 `AddHandler_And_Invoke_CallsHandler` 一致（那里用 `Action<int>` 与 `Invoke([42])`）。`AddHandler(null)` 是无操作，对应 `AddHandler_Null_NoException`。

## 2. 移除处理器

`RemoveHandler` 从尾部向前扫描，移除每个与处理器相等的条目，然后重建缓存：

```csharp
changed.AddHandler(subscriber.Handle);
changed.RemoveHandler(subscriber.Handle);   // matching entries removed from the weak list
changed.Invoke(["nobody"]);
Console.WriteLine($"counter: {counter.Value}");   // still 1
```

**预期结果：** 移除后调用不再触发处理器，对应 `RemoveHandler_StopsInvoking`（它还断言最后一个处理器移除后 `GetInvocationList()` 为 `null`）。相等比较走 `Delegate` 的 `==` 运算符（委托相等：相同目标与方法），不是对象标识。

## 3. 缓存的组合委托（依赖 GC 前先读这一节）

为避免热路径加锁与反射，该类型保留一个*缓存的组合委托*（`_combinedDelegate`，`volatile` 字段）。`GetInvocationList()` 一旦构建就直接返回它（无锁），仅在缓存为空时重建：

```csharp
var typed = changed.GetInvocationList();    // TDelegate? = Action<string>?
typed?.Invoke("hello");                     // typed, reflection-free invocation
```

缓存是一个强组合委托，由此产生两个后果：

- `AddHandler` / `RemoveHandler` 带有 `bool CanUpdateCache = true`。使用默认值时缓存立即重建，**并入缓存的每个存活处理器都会通过它变为强可达**。
- 以 `CanUpdateCache: false` 添加的处理器只写入弱列表，*不*并入缓存。它们保持可回收，因此在下次重建前死掉的订阅者会被 GC 丢弃。

这正是完整代码页上“死处理器”技巧传入 `CanUpdateCache: false` 的原因：

```csharp
var deadSub = new Subscriber(counter);
changed.AddHandler(deadSub.Handle, CanUpdateCache: false);   // keep out of the cache so it can be collected
```

缓存只会在以下时机重建：带 `CanUpdateCache: true` 的 `AddHandler` / `RemoveHandler`、发现缓存为空时的 `GetInvocationList()`，以及 `Clone()` 内部。因此，需要确定性退订时总是调用 `RemoveHandler`；采用“让死订阅者自行脱落”的设计时，用 `CanUpdateCache: false` 添加，然后让后续重建（或 `Clone`）剪除它们。

**预期结果：** 同一处理器添加两次后调用会触发两次；以 `CanUpdateCache: false` 添加第三个处理器，在下次重建前不会改变 `GetInvocationList()` 的返回值。

## 4. 用 Clone 取快照

`Clone()` 返回一个*新的* `WeakDelegate<TDelegate>`，仅由当前存活的弱条目重建，且其缓存已填好——已回收的订阅者直接缺席：

```csharp
var snapshot = changed.Clone();             // rebuilds from live handlers only
snapshot.Invoke(["second"]);
```

**预期结果：** 已回收订阅者的处理器不会通过克隆被调用。这对应测试 `Clone_ReturnsIndependentCopy`（克隆对复制的处理器恰好调用一次）与 `MultipleHandlers_InvokeInRegistrationOrder`（两个处理器按添加顺序触发）。
