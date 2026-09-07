# Weak Types — WeakStack<T>

`WeakStack<T>` (source `Src/Core/VeloxDev.Core/WeakTypes/WeakStack.cs`) is the LIFO counterpart of `WeakQueue<T>`: entries are `WeakReference<T>`, the stack does not keep an item alive, and access methods prune dead entries on the fly. `T` must be a reference type. Good fits are undo/redo stacks and back-navigation buffers of short-lived state that must not pin the objects they were derived from.

All members are guarded by an internal lock, so the type is thread-safe.

## 1. Push and pop (LIFO)

`Push` adds a weak entry (null throws `ArgumentNullException`); `TryPop` returns the topmost live item and removes it; `TryPeek` returns the topmost live item without removing it. Both `Try*` skip collected entries:

```csharp
using System;
using VeloxDev.WeakTypes;

var stack = new WeakStack<Payload>();       // Payload is the helper from the Complete Code page
stack.Push(new Payload(1));
stack.Push(new Payload(2));

Console.WriteLine($"Count: {stack.Count}");             // 2
if (stack.TryPeek(out var top)) Console.WriteLine($"Top: {top}");       // 2 (top, not removed)
while (stack.TryPop(out var item)) Console.WriteLine($"Popped: {item}"); // 2 then 1
Console.WriteLine($"IsEmpty: {stack.IsEmpty}");         // True
```

**Expected result:** items leave in LIFO order (last pushed first) and `TryPeek` leaves the top intact — matching `Push_MultipleItems_LIFO_Order` and `TryPeek_ReturnsTopWithoutRemoving` in `WeakStackTests.cs`.

## 2. Range push, clear, trim

`PushRange(IEnumerable<T>)` adds a batch and returns how many non-null items were pushed; it reverses the enumeration before pushing, so a subsequent series of `TryPop` returns the items in the order you supplied. `Clear()` empties the stack; `TrimExcess()` prunes dead entries and releases spare capacity:

```csharp
var batch = new WeakStack<Payload>();
int added = batch.PushRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**Expected result:** `PushRange` returns the number of non-null items pushed and `Clear` empties the stack — matching `PushRange_AddsMultiple` and `Clear_EmptiesStack`. Passing `null` to `PushRange` throws `ArgumentNullException` (`PushRange_Null_Throws`).

## 3. Enumerate live items

The type implements `IEnumerable<T>`; enumeration prunes first and yields only live entries:

```csharp
var live = stack.ToList();   // only items still reachable
```

**Expected result:** only live entries appear, matching `Enumerable_ReturnsAllLiveItems` in `WeakStackTests.cs`.

## 4. What "weak" changes

As with the queue, the stack never decides an item's lifetime. The unit tests keep their string items alive for the duration of each test, so they pin ordering and API behaviour; they do not assert eviction. The runnable program on the [Verify & Complete Code](../08_verify-and-complete-code/) page shows eviction: `FillStack` pushes two `Payload`s that die at method return, and after `ForceGc` the stack reports `Count: 1` and only the still-alive item is popped. Detailed rules are on the [GC Behavior](../07_gc-behavior/) page.

**Expected result:** you can predict when `Count` drops and which items `TryPop`/`TryPeek` skip after a GC.
