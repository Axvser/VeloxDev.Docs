# 弱引用类型 — `WeakDelegate<TDelegate>`

命名空间 `VeloxDev.WeakTypes`。一个 sealed、泛型、线程安全的多播事件处理器容器，用弱引用而非强引用持有每个处理器，因此拥有 `WeakDelegate<TDelegate>` 的发布者不会永久 root 住它的订阅者。

```csharp
public sealed class WeakDelegate<TDelegate>
    where TDelegate : Delegate
```

`TDelegate` 必须是委托类型 —— 例如 `Action`、`Action<int>`，或自定义的 `delegate`。

内部实现上，每个注册的处理器存为 `List` 里的 `WeakReference<Delegate>`，容器还会把存活处理器经 `Delegate.Combine` 组合成的 *组合委托* 缓存在 `volatile` 字段中；正是这个缓存让常见的「逐个调用所有人」路径无需加锁、无需反射。新增或移除处理器时默认会重建缓存，而重建会先丢弃目标已被回收的处理器。

**关于弱语义的说明。** 缓存的组合委托是对当前已组合处理器的*强引用*。因此以默认 `CanUpdateCache: true` 添加的处理器会一直被容器保活，直到某次重建缓存不再包含它（通常是之后的 `RemoveHandler`）。若想弱语义真正生效，可在添加时传 `CanUpdateCache: false`，让新处理器不进强缓存，从而在其不再被其它对象引用时可以被回收 —— 快速入门探针正是这种用法。

## 方法

### `WeakDelegate<TDelegate>.AddHandler`

**签名：**
`public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `handler` | `TDelegate?` | 要订阅的处理器；`null` 被忽略。 |
| `CanUpdateCache` | `bool` | 为 `true`（默认）时在同一把锁内立即重建组合委托缓存；为 `false` 时只存储处理器，不并入缓存。 |

**返回：** `void`

**说明：**
- 在内部锁内执行。
- `null` 永不抛异常 —— 由 `WeakDelegateTests.AddHandler_Null_NoException` 验证。
- 为什么 `CanUpdateCache` 重要，见上面的类型级说明。

### `WeakDelegate<TDelegate>.RemoveHandler`

**签名：**
`public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `handler` | `TDelegate?` | 要移除的处理器；`null` 不匹配任何项。 |
| `CanUpdateCache` | `bool` | 为 `true`（默认）时在移除后重建组合委托缓存。 |

**返回：** `void`

**说明：**
- 移除每个仍能解析到该委托实例的存储项（对弱持有的目标做引用相等比较）。
- 以默认标志移除后，缓存中的组合委托不再引用该处理器，它因此变得可回收。

### `WeakDelegate<TDelegate>.GetInvocationList`

**签名：**
`public TDelegate? GetInvocationList()`

**返回：** `TDelegate?` — 缓存的组合委托；无存活处理器时为 `null`。

**说明：**
- 尽管名字如此，它返回的是类型为 `TDelegate` 的单个组合委托，而非 `Delegate[]`。这是类型化、无反射的调用入口。
- 无锁快速通道：缓存非空时通过一次 volatile 读直接返回。缓存为 `null` 时容器加锁、剪除已回收处理器、重建缓存再返回结果。
- 添加后返回非 null，由 `WeakDelegateTests.GetInvocationList_ReturnsDelegate` 验证。

### `WeakDelegate<TDelegate>.Invoke`

**签名：**
`public void Invoke(object?[] objects)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `objects` | `object?[]` | 转发给 `DynamicInvoke` 的参数数组。 |

**返回：** `void`

**示例：**
```csharp
// 出处：Src/Core/VeloxDev.Core.Test/WeakTypes/WeakDelegateTests.cs
// 方法：AddHandler_And_Invoke_CallsHandler
var wd = new WeakDelegate<Action<int>>();
int result = 0;
Action<int> handler = x => result = x;

wd.AddHandler(handler);
wd.Invoke([42]);

Assert.AreEqual(42, result);
```

**说明：**
- 用于委托签名未知时的通用路径：调用 `GetInvocationList()?.DynamicInvoke(objects)`。由于走反射，处理器抛出的异常会以 `TargetInvocationException` 形式浮出（`Delegate.DynamicInvoke` 的语义）。
- 编译期已知签名时，优先取 `GetInvocationList()` 做类型化调用 —— 可避免每次调用都走反射。

### `WeakDelegate<TDelegate>.Clone`

**签名：**
`public WeakDelegate<TDelegate> Clone()`

**返回：** `WeakDelegate<TDelegate>` — 仅持有当前存活处理器的独立副本。

**说明：**
- 在锁内遍历存储的处理器，只复制目标仍然存活者，随后计算副本的组合缓存。
- 由 `WeakDelegateTests.Clone_ReturnsIndependentCopy` 与 `MultipleHandlers_CloneInvokesAll` 验证。

## 源文件

`Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs`
