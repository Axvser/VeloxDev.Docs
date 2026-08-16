# Weak Types — `WeakQueue`

底层为 `Queue<WeakReference<T>>`；所有访问都在锁内剪除目标已被回收的条目。

| 成员 | 签名 |
|---|---|
| `Count` | `public int Count { get; }` — 先剪除死亡引用，再返回存活数量 |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Enqueue` | `public void Enqueue(T item)` |
| `EnqueueRange` | `public int EnqueueRange(IEnumerable<T> items)` |
| `TryDequeue` | `public bool TryDequeue(out T? item)` |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |
| `GetEnumerator` | `public IEnumerator<T> GetEnumerator()` |

#### `WeakQueue<T>.Count`

**签名：**
`public int Count { get; }`

**返回：** `int` — 存活（尚未被回收）条目数；先剪除死亡引用。

#### `WeakQueue<T>.IsEmpty`

**签名：**
`public bool IsEmpty { get; }`

**返回：** `bool` — 无存活条目时为 `true`。

#### `WeakQueue<T>.Enqueue`

**签名：**
`public void Enqueue(T item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T` | 要入队的条目。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `item` 为 `null`（由 `WeakQueueTests.Enqueue_Null_Throws` 验证）。 |

**说明：**
- 存储 `new WeakReference<T>(item)` —— 队列不会让条目一直存活。

#### `WeakQueue<T>.EnqueueRange`

**签名：**
`public int EnqueueRange(IEnumerable<T> items)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `items` | `IEnumerable<T>` | 要入队的条目。 |

**返回：** `int` — 实际入队的非 null 条目数。

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `items` 为 `null`。 |

**说明：**
- 返回入队数量（由 `WeakQueueTests.EnqueueRange_AddsMultiple` 验证）。

#### `WeakQueue<T>.TryDequeue`

**签名：**
`public bool TryDequeue(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 出队的条目，或 `null`。 |

**返回：** `bool` — 出队到存活条目为 `true`；队列为空为 `false`。

**说明：**
- 跳过队头的死亡引用；存活条目保持 FIFO 顺序（由 `WeakQueueTests.Enqueue_MultipleItems_FIFO_Order` 验证）。

#### `WeakQueue<T>.TryPeek`

**签名：**
`public bool TryPeek(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 队头存活条目，或 `null`。 |

**返回：** `bool` — 存在存活队头条目为 `true`。

**说明：**
- 窥视不删除条目；队头死亡引用会被丢弃。

#### `WeakQueue<T>.TrimExcess`

**签名：**
`public void TrimExcess()`

**返回：** `void`

**说明：**
- 先剪除死亡引用，再缩减底层 `Queue` 容量。

#### `WeakQueue<T>.Clear`

**签名：**
`public void Clear()`

**返回：** `void`

**说明：**
- 清空队列（由 `WeakQueueTests.Clear_EmptiesQueue` 验证）。
