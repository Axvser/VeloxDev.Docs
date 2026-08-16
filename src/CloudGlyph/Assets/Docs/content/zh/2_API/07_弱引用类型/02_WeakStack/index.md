# Weak Types — `WeakStack`

底层为 `Stack<WeakReference<T>>`；存活条目保持 LIFO 顺序。

| 成员 | 签名 |
|---|---|
| `Count` | `public int Count { get; }` — 先剪除死亡引用 |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Push` | `public void Push(T item)` |
| `PushRange` | `public int PushRange(IEnumerable<T> items)` |
| `TryPop` | `public bool TryPop(out T? item)` |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |
| `GetEnumerator` | `public IEnumerator<T> GetEnumerator()` |

#### `WeakStack<T>.Push`

**签名：**
`public void Push(T item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T` | 要压栈的条目。 |

**返回：** `void`

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `item` 为 `null`（由 `WeakStackTests.Push_Null_Throws` 验证）。 |

#### `WeakStack<T>.PushRange`

**签名：**
`public int PushRange(IEnumerable<T> items)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `items` | `IEnumerable<T>` | 要压栈的条目。 |

**返回：** `int` — 实际压栈的非 null 条目数。

**异常：**
| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `items` 为 `null`。 |

**说明：**
- 反转输入以保证第一个元素位于栈顶（在栈顶保持输入顺序）。

#### `WeakStack<T>.TryPop`

**签名：**
`public bool TryPop(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 出栈的条目，或 `null`。 |

**返回：** `bool` — 出栈到存活条目为 `true`；为空为 `false`。

**说明：**
- 跳过栈顶的死亡引用；存活条目保持 LIFO 顺序（由 `WeakStackTests.Push_MultipleItems_LIFO_Order` 验证）。

#### `WeakStack<T>.TryPeek`

**签名：**
`public bool TryPeek(out T? item)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | `T?` | 栈顶存活条目，或 `null`。 |

**返回：** `bool` — 存在存活栈顶条目为 `true`。
