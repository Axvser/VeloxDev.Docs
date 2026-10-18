# Weak Types — `WeakDelegate<TDelegate>`

Namespace `VeloxDev.WeakTypes`. A sealed, generic, thread-safe container for multicast event handlers that holds each handler by weak reference instead of a strong one, so a publisher that owns a `WeakDelegate<TDelegate>` does not permanently root its subscribers.

```csharp
public sealed class WeakDelegate<TDelegate>
    where TDelegate : Delegate
```

`TDelegate` must be a delegate type — for example `Action`, `Action<int>`, or a custom `delegate`.

Internally each registered handler is stored as `WeakReference<Delegate>` in a list, and the container also caches a *combined delegate* (the result of `Delegate.Combine` over the live handlers) in a `volatile` field. The cache is what makes the common "invoke everyone" path lock-free and reflection-free. Adding or removing a handler rebuilds the cache by default, and a rebuild first drops handlers whose target was already collected.

**Note on weak semantics.** The cached combined delegate is a *strong* reference to the currently combined handlers. A handler added with the default `CanUpdateCache: true` therefore stays reachable through the container until the cache is rebuilt without it (typically a later `RemoveHandler`). Pass `CanUpdateCache: false` at add time to keep the new handler out of the strong cache, so it becomes collectible once nothing else references it — this is the pattern the Quick Start probe exercises. The reprieve lasts until the next rebuild: a handler that is still alive when a rebuild runs is merged into the new strong cache; one that was collected beforehand is dropped.

## Methods

### `WeakDelegate<TDelegate>.AddHandler`

**Signature:**
`public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)`

| Parameter | Type | Description |
|---|---|---|
| `handler` | `TDelegate?` | Handler to subscribe; `null` is ignored. |
| `CanUpdateCache` | `bool` | When `true` (default), rebuilds the combined-delegate cache inside the same lock. When `false`, the handler is stored but not combined into the cache. |

**Returns:** `void`

**Notes:**
- Runs under the internal lock.
- `null` never throws — verified by `WeakDelegateTests.AddHandler_Null_NoException`.
- See the type-level note above for why `CanUpdateCache` matters.

### `WeakDelegate<TDelegate>.RemoveHandler`

**Signature:**
`public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)`

| Parameter | Type | Description |
|---|---|---|
| `handler` | `TDelegate?` | Handler to remove; `null` matches nothing. |
| `CanUpdateCache` | `bool` | When `true` (default), rebuilds the combined-delegate cache after the removals. |

**Returns:** `void`

**Notes:**
- Removes every stored entry whose weakly-held target compares equal to `handler` under the `Delegate` `==` operator (delegate equality: same target and method, not object identity). Because the scan runs from the tail, removing a handler that was added twice removes both entries.
- With the default flag the cache is rebuilt inside the same lock after each matched removal; the cached combined delegate then no longer references the handler, so it becomes collectible.

### `WeakDelegate<TDelegate>.GetInvocationList`

**Signature:**
`public TDelegate? GetInvocationList()`

**Returns:** `TDelegate?` — the cached combined delegate; `null` when no live handlers remain.

**Notes:**
- Despite the name, this returns a single combined delegate of type `TDelegate` — not a `Delegate[]`. It is the typed, reflection-free entry point for invocation.
- Lock-free fast lane: when the cache is non-null it is returned via a plain volatile read. When it is `null`, the container locks, prunes collected handlers, rebuilds the cache and returns the result.
- Verified non-null after an add by `WeakDelegateTests.GetInvocationList_ReturnsDelegate`.

### `WeakDelegate<TDelegate>.Invoke`

**Signature:**
`public void Invoke(object?[] objects)`

| Parameter | Type | Description |
|---|---|---|
| `objects` | `object?[]` | Argument array forwarded to `DynamicInvoke`. |

**Returns:** `void`

**Example:**
```csharp
// Source: Src/Core/VeloxDev.Core.Test/WeakTypes/WeakDelegateTests.cs
// Method: AddHandler_And_Invoke_CallsHandler
var wd = new WeakDelegate<Action<int>>();
int result = 0;
Action<int> handler = x => result = x;

wd.AddHandler(handler);
wd.Invoke([42]);

Assert.AreEqual(42, result);
```

**Notes:**
- Generic path for when the delegate signature is unknown: calls `GetInvocationList()?.DynamicInvoke(objects)`. When no live handler exists the null-conditional makes the call a no-op. Because invocation goes through reflection, an exception thrown by a handler surfaces as `TargetInvocationException` (the semantics of `Delegate.DynamicInvoke`).
- When the signature is known at compile time, prefer taking `GetInvocationList()` and invoking it in a typed way — that avoids reflection on every call.
- The method itself takes no lock; it reads the volatile cache through `GetInvocationList()` and locks only on a cache miss.

### `WeakDelegate<TDelegate>.Clone`

**Signature:**
`public WeakDelegate<TDelegate> Clone()`

**Returns:** `WeakDelegate<TDelegate>` — an independent copy holding the current live handlers.

**Notes:**
- Under lock, iterates the stored handlers, copies only the ones whose target is still alive, then computes the copy's combined cache.
- Verified by `WeakDelegateTests.Clone_ReturnsIndependentCopy`.

## Source

`Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs`
