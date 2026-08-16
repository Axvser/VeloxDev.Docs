# Weak Types — `WeakStack`

Backed by `Stack<WeakReference<T>>`; LIFO order among live items.

| Member | Signature |
|---|---|
| `Count` | `public int Count { get; }` — prunes dead references first |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Push` | `public void Push(T item)` |
| `PushRange` | `public int PushRange(IEnumerable<T> items)` |
| `TryPop` | `public bool TryPop(out T? item)` |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |
| `GetEnumerator` | `public IEnumerator<T> GetEnumerator()` |

#### `WeakStack<T>.Push`

**Signature:**
`public void Push(T item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T` | The item to push. |

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `item` is `null` (verified by `WeakStackTests.Push_Null_Throws`). |

#### `WeakStack<T>.PushRange`

**Signature:**
`public int PushRange(IEnumerable<T> items)`

| Parameter | Type | Description |
|---|---|---|
| `items` | `IEnumerable<T>` | The items to push. |

**Returns:** `int` — the number of non-null items actually pushed.

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentNullException` | `items` is `null`. |

**Notes:**
- Reverses the input so the first element ends up on top (input order preserved on top).

#### `WeakStack<T>.TryPop`

**Signature:**
`public bool TryPop(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The popped item, or `null`. |

**Returns:** `bool` — `true` when a live item was popped; `false` when empty.

**Notes:**
- Skips dead references at the top; LIFO order among live items (verified by `WeakStackTests.Push_MultipleItems_LIFO_Order`).

#### `WeakStack<T>.TryPeek`

**Signature:**
`public bool TryPeek(out T? item)`

| Parameter | Type | Description |
|---|---|---|
| `item` | `T?` | The top live item, or `null`. |

**Returns:** `bool` — `true` when a live top item exists.
