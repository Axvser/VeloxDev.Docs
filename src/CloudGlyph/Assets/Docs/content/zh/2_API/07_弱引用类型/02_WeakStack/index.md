# 弱引用类型 — `WeakStack<T>`

命名空间 `VeloxDev.WeakTypes`。一个线程安全的 LIFO 栈，条目以弱引用持有（`where T : class`）：栈把 `WeakReference<T>` 存入内部 `Stack<WeakReference<T>>`，因此已压栈但被垃圾回收的对象会在后续访问中被跳过，而不是被栈保活。

```csharp
public sealed class WeakStack<T> : IEnumerable<T>
    where T : class
```

该类型实现了 `IEnumerable<T>`，可直接使用 LINQ；枚举只产出仍然存活的条目。所有操作都在内部锁上同步，而计数或枚举这类读取会先剪除已回收引用。

## 属性

### `WeakStack<T>.Count`

**签名：**
`public int Count { get; }`

**返回：** `int` — 目标仍存活的条目数。

**说明：**
- getter 会先（在锁内）剪除已回收引用，因此在存在死引用时并非 O(1)。
- 快速路径：当内部栈完全没有引用时，不取锁直接返回 `0`。

### `WeakStack<T>.IsEmpty`

**签名：**
`public bool IsEmpty { get; }`

**返回：** `bool` — 无存活条目时为 `true`；实现为 `Count == 0`。

## 方法

### `WeakStack<T>.Push`

**签名：**
`public void Push(T item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T` | 要压栈的条目。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `item` 为 `null` —— 由 `WeakStackTests.Push_Null_Throws` 验证。 |

**说明：**
- 存储 `new WeakReference<T>(item)`；栈自身不会让条目一直存活。

### `WeakStack<T>.PushRange`

**签名：**
`public int PushRange(IEnumerable<T> items)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `items` | `IEnumerable<T>` | 要压栈的源集合。 |

**返回：** `int` — 实际压栈的非 null 条目数。

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `items` 为 `null`。 |

**说明：**
- 压栈前会逆序枚举 `items`，因此一批压入的范围再逐个 `TryPop` 出来时保持原始顺序。
- 集合*内部*的 `null` 条目会被跳过；只有非 null 条目会被压栈并计数。集合本身为 `null` 才会抛异常。
- 由 `WeakStackTests.PushRange_AddsMultiple` 与 `PushRange_Null_Throws` 验证。

### `WeakStack<T>.TryPop`

**签名：**
`public bool TryPop(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 方法返回 `true` 时的出栈条目；否则为 `null`。 |

**返回：** `bool` — 出栈到存活条目为 `true`；没有条目剩余为 `false`。

**说明：**
- 不断丢弃栈顶的已回收引用，直到找到存活条目。
- 存活条目保持 LIFO 顺序 —— 由 `WeakStackTests.Push_MultipleItems_LIFO_Order` 验证；空栈由 `WeakStackTests.TryPop_Empty_ReturnsFalse` 验证。

### `WeakStack<T>.TryPeek`

**签名：**
`public bool TryPeek(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 方法返回 `true` 时的存活栈顶条目；否则为 `null`。 |

**返回：** `bool` — 存在存活栈顶条目为 `true`。

**说明：**
- 不删除存活的栈顶条目；扫描过程中会丢弃栈顶的已回收引用 —— 由 `WeakStackTests.TryPeek_ReturnsTopWithoutRemoving` 验证。

### `WeakStack<T>.TrimExcess`

**签名：**
`public void TrimExcess()`

**返回：** `void`

**说明：**
- 先剪除已回收引用，再把底层 `Stack` 的容量缩减到存活数量。

### `WeakStack<T>.Clear`

**签名：**
`public void Clear()`

**返回：** `void`

**说明：**
- 移除全部已存引用；此后 `IsEmpty` 为 `true` —— 由 `WeakStackTests.Clear_EmptiesStack` 验证。

### `WeakStack<T>.GetEnumerator`

**签名：**
`public IEnumerator<T> GetEnumerator()`

**返回：** `IEnumerator<T>` — 遍历存活条目的枚举器。

**说明：**
- 显式 `IEnumerable.GetEnumerator()` 转发到此方法，因此两个接口产出相同序列。
- 在锁内剪除已回收引用，只产出仍然存活的条目 —— 由 `WeakStackTests.Enumerable_ReturnsAllLiveItems` 验证。

## 源文件

`Src/Core/VeloxDev.Core/WeakTypes/WeakStack.cs`
