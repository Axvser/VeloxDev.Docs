# Weak Types — WeakQueue<T>

`WeakQueue<T>` (source `Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs`) is a FIFO buffer whose entries are `WeakReference<T>`. The queue does **not** keep an item alive: an item whose only remaining reference is the queue is collectible. Access methods prune dead entries on the fly, so the collection behaves like a `System.Collections.Generic.Queue<T>` that never pins its contents. `T` must be a reference type.

All members are guarded by an internal lock, so the type is thread-safe.

## 1. Enqueue and dequeue (FIFO)

`Enqueue` appends a weak entry (null throws `ArgumentNullException`); `TryDequeue` returns the front live item and removes it; `TryPeek` returns the front live item without removing it. Both `Try*` skip collected entries:

```csharp
using System;
using VeloxDev.WeakTypes;

var queue = new WeakQueue<Payload>();       // Payload is the helper from the Complete Code page
queue.Enqueue(new Payload(1));
queue.Enqueue(new Payload(2));

Console.WriteLine($"Count: {queue.Count}");             // 2
if (queue.TryPeek(out var head)) Console.WriteLine($"Head: {head}");   // 1 (front, not removed)
while (queue.TryDequeue(out var item)) Console.WriteLine($"Next: {item}");  // 1 then 2
Console.WriteLine($"IsEmpty: {queue.IsEmpty}");         // True
```

**Expected result:** items leave in FIFO order (front first) and `TryPeek` leaves the front intact — matching `Enqueue_MultipleItems_FIFO_Order` and `TryPeek_ReturnsFrontWithoutRemoving` in `WeakQueueTests.cs`.

## 2. Range add, clear, trim

`EnqueueRange(IEnumerable<T>)` appends every non-null item and returns how many were added. `Clear()` empties the buffer. `TrimExcess()` prunes dead entries and releases spare internal capacity:

```csharp
var batch = new WeakQueue<Payload>();
int added = batch.EnqueueRange(new[] { new Payload(3), new Payload(4) });
Console.WriteLine($"added: {added}");       // 2
Console.WriteLine($"Count: {batch.Count}"); // 2

batch.Clear();
Console.WriteLine($"IsEmpty: {batch.IsEmpty}");   // True
```

**Expected result:** `EnqueueRange` returns the number of non-null items enqueued and `Clear` empties the queue — matching `EnqueueRange_AddsMultiple` and `Clear_EmptiesQueue`. Passing `null` to `EnqueueRange` throws `ArgumentNullException` (`EnqueueRange_Null_Throws`).

## 3. Enumerate live items

The type implements `IEnumerable<T>`; enumeration prunes first and yields only live entries, in FIFO order:

```csharp
var seen = new List<Payload>();
foreach (var item in queue) seen.Add(item);   // equivalent to queue.ToList()
```

**Expected result:** only items still reachable appear, matching `Enumerable_ReturnsAllLiveItems` (there with two string items yielding `["a", "b"]`).

## 4. What "weak" changes

Because the queue holds only weak references, the lifespan of a queued item is decided by your code, not by the queue. The unit tests in `WeakQueueTests.cs` keep their string items alive for the duration of the test, so they pin ordering and API behaviour; they do *not* assert eviction. To observe eviction you must let an item lose its last strong reference and then trigger a GC — the runnable program on the [Verify & Complete Code](../08_verify-and-complete-code/) page does exactly that (`FillQueue` enqueues two `Payload`s that die at method return, and after `ForceGc` the queue reports `Count: 1`). The precise rules are on the [GC Behavior](../07_gc-behavior/) page.

**Expected result:** you can predict when `Count` drops and which items `TryDequeue`/`TryPeek` skip after a GC.
