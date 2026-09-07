# 弱引用类型 — `WeakQueue<T>`

命名空间 `VeloxDev.WeakTypes`。一个线程安全的 FIFO 队列，条目以弱引用持有（`where T : class`）：队列把 `WeakReference<T>` 存入内部 `Queue<WeakReference<T>>`，因此已入队但被垃圾回收的对象会在后续访问中被跳过，而不是被队列保活。

```csharp
public sealed class WeakQueue<T> : IEnumerable<T>
    where T : class
```

该类型实现了 `IEnumerable<T>`，可直接使用 LINQ；枚举只产出仍然存活的条目。所有操作都在内部锁上同步，而计数或枚举这类读取会先剪除已回收引用。

## 属性

### `WeakQueue<T>.Count`

**签名：**
`public int Count { get; }`

**返回：** `int` — 目标仍存活的条目数。

**说明：**
- getter 会先（在锁内）剪除已回收引用，因此在存在死引用时并非 O(1)。
- 快速路径：当内部队列完全没有引用时，不取锁直接返回 `0`。

### `WeakQueue<T>.IsEmpty`

**签名：**
`public bool IsEmpty { get; }`

**返回：** `bool` — 无存活条目时为 `true`；实现为 `Count == 0`。

## 方法

### `WeakQueue<T>.Enqueue`

**签名：**
`public void Enqueue(T item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T` | 要入队的条目。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `item` 为 `null` —— 由 `WeakQueueTests.Enqueue_Null_Throws` 验证。 |

**说明：**
- 存储 `new WeakReference<T>(item)`；队列自身不会让条目一直存活。

### `WeakQueue<T>.EnqueueRange`

**签名：**
`public int EnqueueRange(IEnumerable<T> items)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `items` | `IEnumerable<T>` | 要入队的源集合。 |

**返回：** `int` — 实际入队的非 null 条目数。

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `items` 为 `null`。 |

**说明：**
- 集合*内部*的 `null` 条目会被跳过；只有非 null 条目会被入队并计数。集合本身为 `null` 才会抛异常。
- 由 `WeakQueueTests.EnqueueRange_AddsMultiple` 与 `EnqueueRange_Null_Throws` 验证。

### `WeakQueue<T>.TryDequeue`

**签名：**
`public bool TryDequeue(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 方法返回 `true` 时的出队条目；否则为 `null`。 |

**返回：** `bool` — 出队到存活条目为 `true`；没有条目剩余为 `false`。

**说明：**
- 不断丢弃队头的已回收引用，直到找到存活条目。
- 存活条目保持 FIFO 顺序 —— 由 `WeakQueueTests.Enqueue_MultipleItems_FIFO_Order` 验证；空队列由 `WeakQueueTests.TryDequeue_Empty_ReturnsFalse` 验证。

### `WeakQueue<T>.TryPeek`

**签名：**
`public bool TryPeek(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 方法返回 `true` 时的存活队头条目；否则为 `null`。 |

**返回：** `bool` — 存在存活队头条目为 `true`。

**说明：**
- 不删除存活的队头条目；扫描过程中会丢弃队头的已回收引用 —— 由 `WeakQueueTests.TryPeek_ReturnsFrontWithoutRemoving` 验证。

### `WeakQueue<T>.TrimExcess`

**签名：**
`public void TrimExcess()`

**返回：** `void`

**说明：**
- 先剪除已回收引用，再把底层 `Queue` 的容量缩减到存活数量。

### `WeakQueue<T>.Clear`

**签名：**
`public void Clear()`

**返回：** `void`

**说明：**
- 移除全部已存引用；此后 `IsEmpty` 为 `true` —— 由 `WeakQueueTests.Clear_EmptiesQueue` 验证。

### `WeakQueue<T>.GetEnumerator`

**签名：**
`public IEnumerator<T> GetEnumerator()`

**返回：** `IEnumerator<T>` — 按 FIFO 顺序遍历存活条目的枚举器。

**说明：**
- 显式 `IEnumerable.GetEnumerator()` 转发到此方法，因此两个接口产出相同序列。
- 在锁内剪除已回收引用，只产出仍然存活的条目 —— 由 `WeakQueueTests.Enumerable_ReturnsAllLiveItems` 验证。

## 源文件

`Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs`
