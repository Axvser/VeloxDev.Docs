# 弱引用类型 — WeakStack<T>

`WeakStack<T>`（源码 `Src/Core/VeloxDev.Core/WeakTypes/WeakStack.cs`）是 `WeakQueue<T>` 的 LIFO 对应物：条目是 `WeakReference<T>`，栈不会让条目存活，访问方法会即时剪除死条目。`T` 必须是引用类型。适合撤销/重做栈、回退导航缓冲这类由短命状态构成、但又不能把派生它们的对象钉住的场景。

所有成员都由内部锁保护，类型线程安全。

## 1. 压栈与出栈（LIFO）

`Push` 追加一个弱条目（传 null 抛 `ArgumentNullException`）；`TryPop` 返回栈顶存活条目并移除；`TryPeek` 返回栈顶存活条目但不移除。两个 `Try*` 都会跳过已回收条目：

```csharp
using System;
using VeloxDev.WeakTypes;

var stack = new WeakStack<Payload>();       // Payload 是“完整代码”页里的辅助类
stack.Push(new Payload(1));
stack.Push(new Payload(2));

Console.WriteLine($"Count: {stack.Count}");             // 2
if (stack.TryPeek(out var top)) Console.WriteLine($"Top: {top}");       // 2（栈顶，不移除）
while (stack.TryPop(out var item)) Console.WriteLine($"Popped: {item}"); // 依次为 2、1
Console.WriteLine($"IsEmpty: {stack.IsEmpty}");         // True
```

**预期结果：** 条目按 LIFO 顺序离开（最后压入的先出），`TryPeek` 保持栈顶不变 —— 对应 `WeakStackTests.cs` 中的 `Push_MultipleItems_LIFO_Order` 与 `TryPeek_ReturnsTopWithoutRemoving`。

## 2. 批量压栈、清空、裁剪

`PushRange(IEnumerable<T>)` 追加一批条目并返回实际压入的非 null 数量；它在压入前会反转枚举，因此后续一连串 `TryPop` 会按你传入的顺序返回这些条目。`Clear()` 清空栈；`TrimExcess()` 剪除死条目并释放多余容量：

```csharp
var batch = new WeakStack<Payload>();
int added = batch.PushRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**预期结果：** `PushRange` 返回实际压入的非 null 条目数，`Clear` 清空栈 —— 对应 `PushRange_AddsMultiple` 与 `Clear_EmptiesStack`。向 `PushRange` 传 `null` 抛 `ArgumentNullException`（`PushRange_Null_Throws`）。

## 3. 枚举存活条目

类型实现了 `IEnumerable<T>`；枚举先剪除，只产出存活条目：

```csharp
var live = stack.ToList();   // 只有仍可达的条目
```

**预期结果：** 只有存活条目出现，对应 `WeakStackTests.cs` 中的 `Enumerable_ReturnsAllLiveItems`。

## 4. “弱”改变了什么

和队列一样，栈从不决定条目的寿命。单元测试在整个测试期间都让字符串条目存活，因此固定的是顺序与 API 行为，而不断言驱逐。[验证与完整代码](../08_验证与完整代码/)页那个可运行程序展示了驱逐：`FillStack` 压入两个在方法返回时即死的 `Payload`，`ForceGc` 后栈报告 `Count: 1`，只有仍存活的条目被弹出。详细规则见[GC行为与注意](../07_GC行为与注意/)页。

**预期结果：** 你能预测一次 GC 之后 `Count` 何时下降，以及 `TryPop` / `TryPeek` 会跳过哪些条目。
