# Weak Types — `WeakQueue<T>`

Namespace `VeloxDev.WeakTypes`. A thread-safe FIFO queue whose items are held weakly (`where T : class`): the queue stores `WeakReference<T>` entries inside an internal `Queue<WeakReference<T>>`, so an enqueued object that is garbage-collected is skipped on later accesses instead of being kept alive by the queue.

```csharp
public sealed class WeakQueue<T> : IEnumerable<T>
    where T : class
```

The type implements `IEnumerable<T>`, so LINQ works directly; enumeration yields only the items still alive. Every operation is synchronized on an internal lock, and reads that count or enumerate prune collected references first.

## Properties

### `WeakQueue<T>.Count`

**Signature:**
`public int Count { get; }`

**Returns:** `int` — the number of items whose target is still alive.

**Notes:**
- The getter prunes collected references first (under lock), so it is not O(1) while dead references are present.
- Fast path: when the internal queue holds no references at all it returns `0` without locking.

### `WeakQueue<T>.IsEmpty`

**Signature:**
`public bool IsEmpty { get; }`

**Returns:** `bool` — `true` when there are no live items; implemented as `Count == 0`.

## Methods

### `WeakQueue<T>.Enqueue`

**Signature:**
`public void Enqueue(T item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T` | Item to enqueue. |

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `item` is `null` — verified by `WeakQueueTests.Enqueue_Null_Throws`. |

**Notes:**
- Stores `new WeakReference<T>(item)`; the queue never keeps the item alive by itself.

### `WeakQueue<T>.EnqueueRange`

**Signature:**
`public int EnqueueRange(IEnumerable<T> items)`

| Parameter | Type | Description |
|---|---|---|
| `items` | `IEnumerable<T>` | Source collection to enqueue. |

**Returns:** `int` — the number of non-null items actually enqueued.

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `items` is `null`. |

**Notes:**
- `null` items *inside* the collection are skipped; only non-null items are enqueued and counted. A `null` collection itself throws.
- Verified by `WeakQueueTests.EnqueueRange_AddsMultiple` and `EnqueueRange_Null_Throws`.

### `WeakQueue<T>.TryDequeue`

**Signature:**
`public bool TryDequeue(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The dequeued item when the method returns `true`; `null` otherwise. |

**Returns:** `bool` — `true` when a live item was dequeued; `false` when none remains.

**Notes:**
- Removes collected references at the head until a live one is found.
- FIFO order among live items — verified by `WeakQueueTests.Enqueue_MultipleItems_FIFO_Order`; empty queue verified by `WeakQueueTests.TryDequeue_Empty_ReturnsFalse`.

### `WeakQueue<T>.TryPeek`

**Signature:**
`public bool TryPeek(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The live head item when the method returns `true`; `null` otherwise. |

**Returns:** `bool` — `true` when a live head item exists.

**Notes:**
- Does not remove the live head item; collected references at the head are dropped while scanning — verified by `WeakQueueTests.TryPeek_ReturnsFrontWithoutRemoving`.

### `WeakQueue<T>.TrimExcess`

**Signature:**
`public void TrimExcess()`

**Returns:** `void`

**Notes:**
- Prunes collected references, then trims the capacity of the underlying `Queue` down to the live count.

### `WeakQueue<T>.Clear`

**Signature:**
`public void Clear()`

**Returns:** `void`

**Notes:**
- Removes every stored reference; afterwards `IsEmpty` is `true` — verified by `WeakQueueTests.Clear_EmptiesQueue`.

### `WeakQueue<T>.GetEnumerator`

**Signature:**
`public IEnumerator<T> GetEnumerator()`

**Returns:** `IEnumerator<T>` — an enumerator over the live items, in FIFO order.

**Notes:**
- The explicit `IEnumerable.GetEnumerator()` forwards to this method, so both interfaces yield the same sequence.
- Under lock, prunes collected references and yields only the items still alive — verified by `WeakQueueTests.Enumerable_ReturnsAllLiveItems`.

## Source

`Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs`
