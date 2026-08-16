# Weak Types — Quick Start

## Weak Types

### Quick Start

#### 1. Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+); verified against SDK 9.0/10.0 — a *tested* environment. The example targets `net9.0`.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:** none — the four weak-collection types live in `VeloxDev.WeakTypes` and have no runtime dependencies.


#### 2. Install / Add Dependency

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** The command exits `0`; a `<PackageReference Include="VeloxDev.Core" />` is added to the `.csproj` and restore completes. All four types are available on every target framework of the package.

#### 3. Basic Setup / Registration

Instantiate the collection types directly — there is no registration step. The only contract is the generic constraint: queue/stack items and cache keys must be reference types (`class`), and the delegate type must derive from `System.Delegate`.

```csharp
using System;
using VeloxDev.WeakTypes;

var queue = new WeakQueue<Payload>();          // T : class
var stack = new WeakStack<Payload>();          // T : class
var changed = new WeakDelegate<Action<string>>();  // TDelegate : Delegate
var cache = new WeakCache<Payload, string>();  // TTargetKey : class, TCacheKey : class
```

**Expected result:** All four objects construct with no configuration; the collection stores `WeakReference<T>` (or a `ConditionalWeakTable` in the cache) instead of strong references.

#### 4. Core Usage (Step by Step)

**4.1 Enqueue / Push / add a handler**

(`Payload`, `Subscriber` and `Counter` are tiny helper classes defined in the Complete Code below; `queue`, `stack` and `changed` come from step 3.)

```csharp
queue.Enqueue(new Payload(1));      // held weakly
var alive = new Payload(2);
queue.Enqueue(alive);               // still referenced -> survives GC

stack.Push(new Payload(10));        // held weakly

changed.AddHandler(liveSub.Handle); // handler held weakly
```

**Expected result:** Entries whose only reference is the weak one become collectible; `alive` and `liveSub` stay alive because you still hold them.

**4.2 Force a GC and observe sweep-on-access**

```csharp
ForceGc();
Console.WriteLine($"Count after GC: {queue.Count}");   // prunes dead refs first
if (queue.TryDequeue(out var item)) { }                // skips collected entries
```

**Expected result:** `Count` reflects only live items; `TryDequeue` / `TryPop` / `TryPeek` skip entries whose target was collected.

**4.3 Cache add / update / read**

```csharp
cache.AddOrUpdate(key1, "value-100");
if (cache.TryGetCache(key1, out var v)) { }   // O(1) amortized
cache.ForeachCache((k, val) => Console.WriteLine($"{k} -> {val}"));
cache.Remove(key1);
```

**Expected result:** `TryGetCache` returns the value for a live key and `false` for a collected one; `ForeachCache` iterates only live entries.

**4.4 `WeakDelegate` invoke and clone**

```csharp
changed.Invoke(["hello"]);          // DynamicInvoke on the cached combined delegate
var snapshot = changed.Clone();     // rebuilds from live handlers only
snapshot.Invoke(["world"]);
```

**Expected result:** Invoking the clone runs only the handlers whose subscribers are still alive — the collected subscriber's handler is pruned during the rebuild.

#### 5. Verification

Run the complete program below. A sample run (release build, `net9.0`) prints:

```text
== WeakQueue ==
Count after GC: 1
IsEmpty after GC: False
Dequeued: 2

== WeakStack ==
Count after GC: 1
Popped: 2

== WeakDelegate ==
counter after GC + invoke: 1
counter after clone + invoke: 2

== WeakCache ==
TryGetCache(key1): True -> value-100
TryGetCache(new key): False -> (null)
ForeachCache: key=100 value=value-100
TryGetCache(key1) after Remove: False
```

**Expected result:** Items created only inside the helper methods are collected by `ForceGc`, so the queue/stack report `Count: 1` and dequeue/pop only the alive item; the dead delegate handler and dead cache key are skipped.

#### 6. Complete Code

```csharp
using System;
using VeloxDev.WeakTypes;

namespace WeakTypesQuickStart;

// A simple reference-type item that the GC can collect.
public sealed class Payload
{
    public int Value;
    public Payload(int value) => Value = value;
    public override string ToString() => Value.ToString();
}

public sealed class Counter
{
    public int Value;
}

public sealed class Subscriber
{
    private readonly Counter _counter;
    public Subscriber(Counter counter) => _counter = counter;
    public void Handle(string msg) => _counter.Value++;
}

public static class Program
{
    public static void Main()
    {
        Console.WriteLine("== WeakQueue ==");
        var queue = new WeakQueue<Payload>();
        FillQueue(queue);
        var alive = new Payload(2);
        queue.Enqueue(alive);
        ForceGc();
        Console.WriteLine($"Count after GC: {queue.Count}");
        Console.WriteLine($"IsEmpty after GC: {queue.IsEmpty}");
        while (queue.TryDequeue(out var item))
        {
            Console.WriteLine($"Dequeued: {item}");
        }

        Console.WriteLine();
        Console.WriteLine("== WeakStack ==");
        var stack = new WeakStack<Payload>();
        FillStack(stack);
        stack.Push(alive);
        ForceGc();
        Console.WriteLine($"Count after GC: {stack.Count}");
        while (stack.TryPop(out var item))
        {
            Console.WriteLine($"Popped: {item}");
        }

        Console.WriteLine();
        Console.WriteLine("== WeakDelegate ==");
        var changed = new WeakDelegate<Action<string>>();
        var counter = new Counter();
        var liveSub = new Subscriber(counter);
        changed.AddHandler(liveSub.Handle);
        AddDeadHandler(changed, counter);
        ForceGc();
        changed.Invoke(["first"]);
        Console.WriteLine($"counter after GC + invoke: {counter.Value}");
        var snapshot = changed.Clone();
        snapshot.Invoke(["second"]);
        Console.WriteLine($"counter after clone + invoke: {counter.Value}");

        Console.WriteLine();
        Console.WriteLine("== WeakCache ==");
        var cache = new WeakCache<Payload, string>();
        var key1 = new Payload(100);
        cache.AddOrUpdate(key1, "value-100");
        AddDeadCacheEntry(cache);
        ForceGc();
        Console.WriteLine($"TryGetCache(key1): {cache.TryGetCache(key1, out var v1)} -> {v1}");
        Console.WriteLine($"TryGetCache(new key): {cache.TryGetCache(new Payload(200), out var v2)} -> {v2 ?? "(null)"}");
        cache.ForeachCache((k, v) => Console.WriteLine($"ForeachCache: key={k.Value} value={v}"));
        cache.Remove(key1);
        Console.WriteLine($"TryGetCache(key1) after Remove: {cache.TryGetCache(key1, out _)}");
        GC.KeepAlive(alive);
        GC.KeepAlive(liveSub);
    }

    // Items created here go out of scope when the method returns, so only the
    // weak reference keeps them reachable; the next GC collects them.
    private static void FillQueue(WeakQueue<Payload> queue)
    {
        queue.Enqueue(new Payload(1));
        queue.Enqueue(new Payload(3));
    }

    private static void FillStack(WeakStack<Payload> stack)
    {
        stack.Push(new Payload(10));
        stack.Push(new Payload(30));
    }

    private static void AddDeadHandler(WeakDelegate<Action<string>> changed, Counter counter)
    {
        var deadSub = new Subscriber(counter);
        // CanUpdateCache:false avoids eagerly building the combined-delegate cache,
        // which would otherwise keep the dead subscriber alive.
        changed.AddHandler(deadSub.Handle, CanUpdateCache: false);
    }

    private static void AddDeadCacheEntry(WeakCache<Payload, string> cache)
    {
        cache.AddOrUpdate(new Payload(200), "value-200");
    }

    private static void ForceGc()
    {
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
    }
}
```

#### 7. Run Declaration

- ✅ Actually built and ran on 2026-08-17 (`dotnet run -c Release`, target `net9.0`). Recorded output (see §5): `WeakQueue Count after GC: 1`, `Dequeued: 2`; `WeakStack Count after GC: 1`, `Popped: 2`; `WeakDelegate counter after GC + invoke: 1`, `counter after clone + invoke: 2`; `WeakCache TryGetCache(key1): True -> value-100`, `TryGetCache(new key): False`, `ForeachCache: key=100 value=value-100`, `TryGetCache(key1) after Remove: False`.
