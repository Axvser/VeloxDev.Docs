# Weak Types — `WeakQueue`

Backed by `Queue<WeakReference<T>>`; every access under a lock prunes entries whose target was collected.

| Member | Signature |
|---|---|
| `Count` | `public int Count { get; }` — prunes dead references first, then returns the live count |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Enqueue` | `public void Enqueue(T item)` |
| `EnqueueRange` | `public int EnqueueRange(IEnumerable<T> items)` |
| `TryDequeue` | `public bool TryDequeue(out T? item)` |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |
| `GetEnumerator` | `public IEnumerator<T> GetEnumerator()` |

#### `WeakQueue<T>.Count`

**Signature:**
`public int Count { get; }`

**Returns:** `int` — number of live (not-yet-collected) items; dead references are pruned first.

#### `WeakQueue<T>.IsEmpty`

**Signature:**
`public bool IsEmpty { get; }`

**Returns:** `bool` — `true` when there are no live items.

#### `WeakQueue<T>.Enqueue`

**Signature:**
`public void Enqueue(T item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T` | The item to enqueue. |

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `item` is `null` (verified by `WeakQueueTests.Enqueue_Null_Throws`). |

**Notes:**
- Stores `new WeakReference<T>(item)` — the queue does not keep the item alive.

#### `WeakQueue<T>.EnqueueRange`

**Signature:**
`public int EnqueueRange(IEnumerable<T> items)`

| Parameter | Type | Description |
|---|---|---|
| `items` | `IEnumerable<T>` | The items to enqueue. |

**Returns:** `int` — the number of non-null items actually enqueued.

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `items` is `null`. |

**Notes:**
- Returns the enqueued count (verified by `WeakQueueTests.EnqueueRange_AddsMultiple`).

#### `WeakQueue<T>.TryDequeue`

**Signature:**
`public bool TryDequeue(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The dequeued item, or `null`. |

**Returns:** `bool` — `true` when a live item was dequeued; `false` when the queue is empty.

**Notes:**
- Skips dead references at the front; FIFO order among live items (verified by `WeakQueueTests.Enqueue_MultipleItems_FIFO_Order`).

#### `WeakQueue<T>.TryPeek`

**Signature:**
`public bool TryPeek(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The front live item, or `null`. |

**Returns:** `bool` — `true` when a live front item exists.

**Notes:**
- Peek does not remove the item; dead front references are dropped.

#### `WeakQueue<T>.TrimExcess`

**Signature:**
`public void TrimExcess()`

**Returns:** `void`

**Notes:**
- Prunes dead references, then trims the underlying `Queue` capacity.

#### `WeakQueue<T>.Clear`

**Signature:**
`public void Clear()`

**Returns:** `void`

**Notes:**
- Empties the queue (verified by `WeakQueueTests.Clear_EmptiesQueue`).
