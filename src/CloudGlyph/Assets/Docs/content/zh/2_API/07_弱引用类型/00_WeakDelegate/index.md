# Weak Types — `WeakDelegate`

```csharp
public sealed class WeakDelegate<TDelegate> where TDelegate : Delegate
{
    private volatile TDelegate? _combinedDelegate;
    private readonly List<WeakReference<Delegate>> _handlers = [];
}
```

把处理器存为 `WeakReference<Delegate>`，并缓存组合委托，以便在热路径上无锁、无反射地调用。

#### `WeakDelegate<TDelegate>.AddHandler`

**签名：**
`public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `handler` | `TDelegate?` | 要订阅的委托；`null` 被忽略。 |
| `CanUpdateCache` | `bool` | 为 `true`（默认）时立即重建组合委托缓存。 |

**返回：** `void`

**说明：**
- 以默认 `CanUpdateCache: true` 添加会立刻构建强引用的组合委托，它会一直保住所有处理器直到缓存被重建。希望弱语义在下次 GC 后生效时传 `false`（快速入门探针即如此使用）。

#### `WeakDelegate<TDelegate>.RemoveHandler`

**签名：**
`public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `handler` | `TDelegate?` | 要移除的委托；`null` 被忽略。 |
| `CanUpdateCache` | `bool` | 为 `true` 时在移除后重建缓存。 |

**返回：** `void`

**说明：**
- 移除所有匹配引用；由 `WeakDelegateTests.RemoveHandler_RemovesFromHandlerList` 验证。

#### `WeakDelegate<TDelegate>.GetInvocationList`

**签名：**
`public TDelegate? GetInvocationList()`

**返回：** `TDelegate?` — 缓存的组合委托；无存活处理器时为 `null`。

**说明：**
- 无锁快速路径：通过 volatile 读取返回缓存的 `_combinedDelegate`。缓存为 `null` 时在锁内重建 —— `RebuildCache` 先剪除已回收处理器，再组合幸存者。

#### `WeakDelegate<TDelegate>.Invoke`

**签名：**
`public void Invoke(object?[] objects)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `objects` | `object?[]` | 传给 `DynamicInvoke` 的参数数组。 |

**返回：** `void`

**示例：**
```text
// 出处：Src/Core/VeloxDev.Core.Test/WeakTypes/WeakDelegateTests.cs（第 17 行）
wd.Invoke([42]);
```

**说明：**
- 用于未知签名的通用调用；已知委托签名时，优先用 `GetInvocationList()` 做类型化调用以避免反射。

#### `WeakDelegate<TDelegate>.Clone`

**签名：**
`public WeakDelegate<TDelegate> Clone()`

**返回：** `WeakDelegate<TDelegate>` — 仅由存活处理器重建的独立副本。

**说明：**
- 通过 `TryGetTarget` 遍历 `_handlers` 重建，跳过已回收目标。由 `WeakDelegateTests.Clone_ReturnsIndependentCopy` 与 `MultipleHandlers_CloneInvokesAll` 验证。
