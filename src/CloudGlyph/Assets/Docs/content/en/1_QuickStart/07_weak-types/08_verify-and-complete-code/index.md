# Weak Types — Verify & Complete Code

## 1. Verify with the automated tests

The behavioural evidence lives in the MSTest suite under `Src/Core/VeloxDev.Core.Test/WeakTypes/`. Running only the weak-types tests on 2026-09-07 against the current `master` produced:

```text
总共 1 个测试文件与指定模式相匹配。
已通过! - 失败:     0，通过:    33，已跳过:     0，总计:    33，持续时间: 39 ms - VeloxDev.Core.Test.dll (net10.0)
```

That is `dotnet test --filter "FullyQualifiedName~WeakTypes" -c Release` on the `VeloxDev.Core.Test` project (target `net10.0`): 33 tests across `WeakDelegateTests` (6), `WeakQueueTests` (10), `WeakStackTests` (10) and `WeakCacheTests` (7), all green. The tests pin the API surface and ordering rules but deliberately avoid asserting GC eviction (the string keys and short-lived items in the tests are rooted for the duration of each test) — see the [GC Behavior](../07_gc-behavior/) page.

**Expected result:** `dotnet test` on `VeloxDev.Core.Test` runs the `WeakTypes` tests green.

## 2. Complete code

A single self-contained console program (target `net10.0`) that exercises all four types. Each "dead" `Payload`/handler/key is created inside a helper method so it is unreachable after the helper returns; `ForceGc` then collects it, and the console reports only the surviving items. All `using` directives are explicit; the only external requirement is a reference to `VeloxDev.Core` (page [Install](../01_install/)):

```csharp
using System;
using VeloxDev.WeakTypes;

namespace WeakTypesQuickStart
{
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
        public void Handle(string message) => _counter.Value++;
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
            while (queue.TryDequeue(out var dequeued))
            {
                Console.WriteLine($"Dequeued: {dequeued}");
            }

            Console.WriteLine();
            Console.WriteLine("== WeakStack ==");
            var stack = new WeakStack<Payload>();
            FillStack(stack);
            stack.Push(alive);
            ForceGc();
            Console.WriteLine($"Count after GC: {stack.Count}");
            while (stack.TryPop(out var popped))
            {
                Console.WriteLine($"Popped: {popped}");
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
            GC.KeepAlive(counter);
        }

        // Items created here become unreachable when the method returns, so only the
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
            // CanUpdateCache:false avoids rebuilding the combined-delegate cache,
            // which would otherwise keep the dead subscriber alive through the cache.
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
}
```

## 3. Recorded output

The transcript below is the verbatim console output of one `Release` run (see the run declaration). It is stable because every dead object is created inside a helper method whose frame has already returned before the GC runs:

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

## 4. Reading the output against the pages

- `WeakQueue` / `WeakStack`: the `Payload(1)`/`Payload(3)` (queue) and `Payload(10)`/`Payload(30)` (stack) created inside the fill helpers were collected, so `Count after GC: 1` and only the still-alive `alive` item (`Value = 2`) is dequeued/popped (pages [WeakQueue](../04_weak-queue/) and [WeakStack](../05_weak-stack/), and the sweep rules on [GC Behavior](../07_gc-behavior/)).
- `WeakDelegate`: the dead subscriber added with `CanUpdateCache: false` was collected, so the first invoke fires only `liveSub` (`counter` 1); `Clone()` then rebuilds from live handlers and the clone's invoke raises it to 2 (page [WeakDelegate](../03_weak-delegate/)).
- `WeakCache`: the dead `Payload(200)` key was collected, so `TryGetCache` on a brand-new key is `False`, and `ForeachCache` visits only `key1` (`key=100 value=value-100`); `Remove(key1)` then makes the lookup `False` (page [WeakCache](../06_weak-cache/)).

## 5. Run declaration

- ✅ Actually built and ran on 2026-09-07 (`dotnet run -c Release`, target `net10.0`, against a project reference to `VeloxDev.Core` from this repository). Recorded output is shown verbatim in section 3; three consecutive runs produced identical output. The complete `WeakTypes` MSTest suite (33/33) was also executed green on the same date (section 1).
