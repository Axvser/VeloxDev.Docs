# Weak Types — `WeakStack<T>`

Namespace `VeloxDev.WeakTypes`. A thread-safe LIFO stack whose items are held weakly (`where T : class`): the stack stores `WeakReference<T>` entries inside an internal `Stack<WeakReference<T>>`, so a pushed object that is garbage-collected is skipped on later accesses instead of being kept alive by the stack.

```csharp
public sealed class WeakStack<T> : IEnumerable<T>
    where T : class
```

The type implements `IEnumerable<T>`, so LINQ works directly; enumeration yields only the items still alive. Every operation is synchronized on an internal lock, and reads that count or enumerate prune collected references first.

## Properties

### `WeakStack<T>.Count`

**Signature:**
`public int Count { get; }`

**Returns:** `int` — the number of items whose target is still alive.

**Notes:**
- The getter prunes collected references first (under lock), so it is not O(1) while dead references are present.
- Fast path: when the internal stack holds no references at all it returns `0` without locking.

### `WeakStack<T>.IsEmpty`

**Signature:**
`public bool IsEmpty { get; }`

**Returns:** `bool` — `true` when there are no live items; implemented as `Count == 0`.

## Methods

### `WeakStack<T>.Push`

**Signature:**
`public void Push(T item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T` | Item to push. |

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `item` is `null` — verified by `WeakStackTests.Push_Null_Throws`. |

**Notes:**
- Stores `new WeakReference<T>(item)`; the stack never keeps the item alive by itself.

### `WeakStack<T>.PushRange`

**Signature:**
`public int PushRange(IEnumerable<T> items)`

| Parameter | Type | Description |
|---|---|---|
| `items` | `IEnumerable<T>` | Source collection to push. |

**Returns:** `int` — the number of non-null items actually pushed.

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `items` is `null`. |

**Notes:**
- Enumerates `items` in reverse before pushing, so a range pushed together is popped back in its original order.
- `null` items *inside* the collection are skipped; only non-null items are pushed and counted. A `null` collection itself throws.
- Verified by `WeakStackTests.PushRange_AddsMultiple` and `PushRange_Null_Throws`.

### `WeakStack<T>.TryPop`

**Signature:**
`public bool TryPop(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The popped item when the method returns `true`; `null` otherwise. |

**Returns:** `bool` — `true` when a live item was popped; `false` when none remains.

**Notes:**
- Removes collected references at the top until a live one is found.
- LIFO order among live items — verified by `WeakStackTests.Push_MultipleItems_LIFO_Order`; empty stack verified by `WeakStackTests.TryPop_Empty_ReturnsFalse`.

### `WeakStack<T>.TryPeek`

**Signature:**
`public bool TryPeek(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The live top item when the method returns `true`; `null` otherwise. |

**Returns:** `bool` — `true` when a live top item exists.

**Notes:**
- Does not remove the live top item; collected references at the top are dropped while scanning — verified by `WeakStackTests.TryPeek_ReturnsTopWithoutRemoving`.

### `WeakStack<T>.TrimExcess`

**Signature:**
`public void TrimExcess()`

**Returns:** `void`

**Notes:**
- Prunes collected references, then trims the capacity of the underlying `Stack` down to the live count.

### `WeakStack<T>.Clear`

**Signature:**
`public void Clear()`

**Returns:** `void`

**Notes:**
- Removes every stored reference; afterwards `IsEmpty` is `true` — verified by `WeakStackTests.Clear_EmptiesStack`.

### `WeakStack<T>.GetEnumerator`

**Signature:**
`public IEnumerator<T> GetEnumerator()`

**Returns:** `IEnumerator<T>` — an enumerator over the live items.

**Notes:**
- The explicit `IEnumerable.GetEnumerator()` forwards to this method, so both interfaces yield the same sequence.
- Under lock, prunes collected references and yields only the items still alive — verified by `WeakStackTests.Enumerable_ReturnsAllLiveItems`.

## Source

`Src/Core/VeloxDev.Core/WeakTypes/WeakStack.cs`
