# 弱引用类型 — `WeakStack<T>`

`WeakStack<T>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakStack.cs`）是 `WeakQueue<T>` 的 LIFO 对应物：条目为 `WeakReference<T>`，栈不会让条目存活，访问方法会随手剪除死条目。`T` 必须是引用类型。适合撤销/重做栈，以及由短命状态导出、又不能钉住其来源对象的返回导航缓冲。

所有成员都由内部锁保护，因此类型是线程安全的。

## 1. 压栈与出栈（LIFO）

`Push` 添加一个弱条目（null 抛 `ArgumentNullException`）；`TryPop` 返回并移除栈顶存活条目；`TryPeek` 返回栈顶存活条目但不移除。两个 `Try*` 都会跳过已回收条目：

```csharp
using System;
using VeloxDev.WeakTypes;

var stack = new WeakStack<Payload>();       // Payload is the helper from the Complete Code page
var first = new Payload(1);                 // keep locals alive so Count is deterministic
var second = new Payload(2);
stack.Push(first);
stack.Push(second);

Console.WriteLine($"Count: {stack.Count}");             // 2
if (stack.TryPeek(out var top)) Console.WriteLine($"Top: {top}");       // 2 (top, not removed)
while (stack.TryPop(out var item)) Console.WriteLine($"Popped: {item}"); // 2 then 1
Console.WriteLine($"IsEmpty: {stack.IsEmpty}");         // True
GC.KeepAlive(first);
GC.KeepAlive(second);
```

**预期结果：** 条目按 LIFO 顺序（最后压入者先出）离开，且 `TryPeek` 保留栈顶不变——对应 `WeakStackTests.cs` 中的 `Push_MultipleItems_LIFO_Order` 与 `TryPeek_ReturnsTopWithoutRemoving`。`GC.KeepAlive` 调用让载荷在代码片段期间保持可达。

## 2. 批量压栈、清空、裁剪

`PushRange(IEnumerable<T>)` 批量添加并返回压入的非 null 条目数；它先反转枚举再压栈，因此随后连续 `TryPop` 会按你提供的顺序返回条目。`Clear()` 清空栈；`TrimExcess()` 剪除死条目并释放多余容量：

```csharp
var batch = new WeakStack<Payload>();
int added = batch.PushRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**预期结果：** `PushRange` 返回实际压入的非 null 条目数，`Clear` 清空栈——对应 `PushRange_AddsMultiple` 与 `Clear_EmptiesStack`。向 `PushRange` 传 `null` 会抛 `ArgumentNullException`（`PushRange_Null_Throws`）。

## 3. 枚举存活条目

该类型实现 `IEnumerable<T>`；枚举先剪除，再只产出存活条目：

```csharp
var live = stack.ToList();   // only items still reachable
```

**预期结果：** 只有存活条目出现，对应 `WeakStackTests.cs` 中的 `Enumerable_ReturnsAllLiveItems`。

## 4. “弱”改变了什么

与队列一样，栈从不决定条目寿命。单测在每个测试期间保持字符串条目存活，因此钉住的是顺序与 API 行为，并不断言驱逐。验证与完整代码页的可运行程序展示了驱逐：`FillStack` 压入两个在方法返回时死亡的 `Payload`，`ForceGc` 之后栈报告 `Count: 1`，并且只弹出仍存活的条目。详细规则见 GC 行为页。

**预期结果：** GC 之后，你能预测 `Count` 何时下降，以及 `TryPop`/`TryPeek` 会跳过哪些条目。
