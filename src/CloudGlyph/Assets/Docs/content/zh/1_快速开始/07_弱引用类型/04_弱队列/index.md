# 弱引用类型 — WeakQueue<T>

`WeakQueue<T>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs`）是一个条目为 `WeakReference<T>` 的 FIFO 缓冲。队列**不会**让条目存活：一个只剩下队列引用的条目是可回收的。访问方法会即时剪除死条目，因此这个集合用起来像永远不会钉住内容的 `System.Collections.Generic.Queue<T>`。`T` 必须是引用类型。

所有成员都由内部锁保护，类型线程安全。

## 1. 入队与出队（FIFO）

`Enqueue` 追加一个弱条目（传 null 抛 `ArgumentNullException`）；`TryDequeue` 返回队首存活条目并移除；`TryPeek` 返回队首存活条目但不移除。两个 `Try*` 都会跳过已回收条目：

```csharp
using System;
using VeloxDev.WeakTypes;

var queue = new WeakQueue<Payload>();       // Payload 是“完整代码”页里的辅助类
queue.Enqueue(new Payload(1));
queue.Enqueue(new Payload(2));

Console.WriteLine($"Count: {queue.Count}");             // 2
if (queue.TryPeek(out var head)) Console.WriteLine($"Head: {head}");   // 1（队首，不移除）
while (queue.TryDequeue(out var item)) Console.WriteLine($"Next: {item}");  // 依次为 1、2
Console.WriteLine($"IsEmpty: {queue.IsEmpty}");         // True
```

**预期结果：** 条目按 FIFO 顺序离开（队首先出），`TryPeek` 保持队首不变 —— 对应 `WeakQueueTests.cs` 中的 `Enqueue_MultipleItems_FIFO_Order` 与 `TryPeek_ReturnsFrontWithoutRemoving`。

## 2. 批量入队、清空、裁剪

`EnqueueRange(IEnumerable<T>)` 追加每个非 null 条目，并返回实际追加的数量。`Clear()` 清空缓冲。`TrimExcess()` 剪除死条目并释放多余内部容量：

```csharp
var batch = new WeakQueue<Payload>();
int added = batch.EnqueueRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**预期结果：** `EnqueueRange` 返回实际入队的非 null 条目数，`Clear` 清空队列 —— 对应 `EnqueueRange_AddsMultiple` 与 `Clear_EmptiesQueue`。向 `EnqueueRange` 传 `null` 抛 `ArgumentNullException`（`EnqueueRange_Null_Throws`）。

## 3. 枚举存活条目

类型实现了 `IEnumerable<T>`；枚举先剪除，只产出存活条目，顺序为 FIFO：

```csharp
var seen = new List<Payload>();
foreach (var item in queue) seen.Add(item);   // 等价于 queue.ToList()
```

**预期结果：** 只有仍可达的条目出现，对应 `Enumerable_ReturnsAllLiveItems`（那里以两个字符串条目得到 `["a", "b"]`）。

## 4. “弱”改变了什么

因为队列只持有弱引用，一个排队条目的寿命由你的代码决定，而不是由队列决定。`WeakQueueTests.cs` 里的单元测试在整个测试期间都让字符串条目存活，所以它们固定的是顺序与 API 行为，而*不*断言驱逐。要观察驱逐，你得让条目失去最后一个强引用再触发一次 GC —— [验证与完整代码](../08_验证与完整代码/)页那个可运行程序正是这么做的（`FillQueue` 入队两个在方法返回时即死的 `Payload`，`ForceGc` 后队列报告 `Count: 1`）。精确规则见[GC行为与注意](../07_GC行为与注意/)页。

**预期结果：** 你能预测一次 GC 之后 `Count` 何时下降，以及 `TryDequeue` / `TryPeek` 会跳过哪些条目。
