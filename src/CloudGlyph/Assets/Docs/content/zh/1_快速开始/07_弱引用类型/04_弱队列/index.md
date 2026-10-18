# 弱引用类型 — `WeakQueue<T>`

`WeakQueue<T>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs`）是一个 FIFO 缓冲区，条目为 `WeakReference<T>`。队列**不会**让条目存活：唯一剩余引用是队列的条目可被回收。访问方法会随手剪除死条目，因此其行为像一个从不钉住内容的 `System.Collections.Generic.Queue<T>`。`T` 必须是引用类型。

所有成员都由内部锁保护，因此类型是线程安全的。

## 1. 入队与出队（FIFO）

`Enqueue` 追加一个弱条目（null 抛 `ArgumentNullException`）；`TryDequeue` 返回并移除队首存活条目；`TryPeek` 返回队首存活条目但不移除。两个 `Try*` 都会跳过已回收条目：

```csharp
using System;
using VeloxDev.WeakTypes;

var queue = new WeakQueue<Payload>();       // Payload is the helper from the Complete Code page
var first = new Payload(1);                 // keep locals alive so Count is deterministic
var second = new Payload(2);
queue.Enqueue(first);
queue.Enqueue(second);

Console.WriteLine($"Count: {queue.Count}");             // 2
if (queue.TryPeek(out var head)) Console.WriteLine($"Head: {head}");   // 1 (front, not removed)
while (queue.TryDequeue(out var item)) Console.WriteLine($"Next: {item}");  // 1 then 2
Console.WriteLine($"IsEmpty: {queue.IsEmpty}");         // True
GC.KeepAlive(first);
GC.KeepAlive(second);
```

**预期结果：** 条目按 FIFO 顺序（队首先出）离开，且 `TryPeek` 保留队首不变——对应 `WeakQueueTests.cs` 中的 `Enqueue_MultipleItems_FIFO_Order` 与 `TryPeek_ReturnsFrontWithoutRemoving`。两个 `GC.KeepAlive` 调用让载荷保持强可达，因此 `Count` 不会在语句之间下降；没有它们时，仅靠队列不会让条目存活。

## 2. 批量入队、清空、裁剪

`EnqueueRange(IEnumerable<T>)` 追加每个非 null 条目并返回添加数量。`Clear()` 清空缓冲区。`TrimExcess()` 剪除死条目并释放多余内部容量：

```csharp
var batch = new WeakQueue<Payload>();
int added = batch.EnqueueRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**预期结果：** `EnqueueRange` 返回实际入队的非 null 条目数，`Clear` 清空队列——对应 `EnqueueRange_AddsMultiple` 与 `Clear_EmptiesQueue`。向 `EnqueueRange` 传 `null` 会抛 `ArgumentNullException`（`EnqueueRange_Null_Throws`）。

## 3. 枚举存活条目

该类型实现 `IEnumerable<T>`；枚举先剪除，再按 FIFO 顺序只产出存活条目：

```csharp
var seen = new List<Payload>();
foreach (var item in queue) seen.Add(item);   // equivalent to queue.ToList()
```

**预期结果：** 只有仍可达的条目出现，对应 `Enumerable_ReturnsAllLiveItems`（那里用两个字符串条目产出 `["a", "b"]`）。

## 4. “弱”改变了什么

由于队列只持弱引用，条目寿命由你的代码而非队列决定。`WeakQueueTests.cs` 中的单测在整个测试期间让字符串条目保持存活，因此它们钉住的是顺序与 API 行为，*不*断言驱逐。要观察驱逐，必须让条目失去最后的强引用并触发 GC——验证与完整代码页的可运行程序正是如此（`FillQueue` 入队两个在方法返回时死亡的 `Payload`，`ForceGc` 之后队列报告 `Count: 1`）。确切规则见 GC 行为页。

**预期结果：** GC 之后，你能预测 `Count` 何时下降，以及 `TryDequeue`/`TryPeek` 会跳过哪些条目。
