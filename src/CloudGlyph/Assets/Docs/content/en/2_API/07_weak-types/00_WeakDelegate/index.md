# Weak Types — `WeakDelegate`

```csharp
public sealed class WeakDelegate<TDelegate> where TDelegate : Delegate
{
    private volatile TDelegate? _combinedDelegate;
    private readonly List<WeakReference<Delegate>> _handlers = [];
}
```

Stores handlers as `WeakReference<Delegate>` and caches a combined delegate for lock-free, reflection-free invocation on the hot path.

#### `WeakDelegate<TDelegate>.AddHandler`

**Signature:**
`public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)`

| Parameter | Type | Description |
|---|---|---|
| `handler` | `TDelegate?` | The delegate to subscribe; `null` is ignored. |
| `CanUpdateCache` | `bool` | When `true` (default), rebuilds the combined-delegate cache immediately. |

**Returns:** `void`

**Notes:**
- Adding with the default `CanUpdateCache: true` eagerly builds a strong combined delegate, which keeps every handler alive until the cache is rebuilt. Pass `false` when you want the weak semantics to take effect after the next GC (used by the Quick Start probe).

#### `WeakDelegate<TDelegate>.RemoveHandler`

**Signature:**
`public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)`

| Parameter | Type | Description |
|---|---|---|
| `handler` | `TDelegate?` | The delegate to remove; `null` is ignored. |
| `CanUpdateCache` | `bool` | When `true`, rebuilds the cache after removal. |

**Returns:** `void`

**Notes:**
- Removes all matching references; verified by `WeakDelegateTests.RemoveHandler_RemovesFromHandlerList`.

#### `WeakDelegate<TDelegate>.GetInvocationList`

**Signature:**
`public TDelegate? GetInvocationList()`

**Returns:** `TDelegate?` — the cached combined delegate, or `null` when no live handlers remain.

**Notes:**
- Lock-free fast path: returns the cached `_combinedDelegate` via a volatile read. When the cache is `null`, it rebuilds under lock — `RebuildCache` prunes collected handlers first and combines the survivors.

#### `WeakDelegate<TDelegate>.Invoke`

**Signature:**
`public void Invoke(object?[] objects)`

| Parameter | Type | Description |
|---|---|---|
| `objects` | `object?[]` | The argument array passed to `DynamicInvoke`. |

**Returns:** `void`

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/WeakTypes/WeakDelegateTests.cs (line 17)
wd.Invoke([42]);
```

**Notes:**
- Generic invocation for unknown signatures; when the delegate signature is known, prefer `GetInvocationList()` and call it in a typed way to avoid reflection.

#### `WeakDelegate<TDelegate>.Clone`

**Signature:**
`public WeakDelegate<TDelegate> Clone()`

**Returns:** `WeakDelegate<TDelegate>` — an independent copy rebuilt from live handlers only.

**Notes:**
- Rebuilds from `_handlers` via `TryGetTarget`, skipping collected targets. Verified by `WeakDelegateTests.Clone_ReturnsIndependentCopy` and `MultipleHandlers_CloneInvokesAll`.
