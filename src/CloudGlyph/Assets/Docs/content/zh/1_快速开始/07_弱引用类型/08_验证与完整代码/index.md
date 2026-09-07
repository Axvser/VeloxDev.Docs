# 弱引用类型 — 验证与完整代码

## 1. 用自动化测试验证

行为证据位于 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 下的 MSTest 套件。2026-09-07 只跑弱类型测试、对应当前 `master`，得到：

```text
总共 1 个测试文件与指定模式相匹配。
已通过! - 失败:     0，通过:    33，已跳过:     0，总计:    33，持续时间: 39 ms - VeloxDev.Core.Test.dll (net10.0)
```

这是对 `VeloxDev.Core.Test` 项目（目标 `net10.0`）执行 `dotnet test --filter "FullyQualifiedName~WeakTypes" -c Release`：跨 `WeakDelegateTests`（6）、`WeakQueueTests`（10）、`WeakStackTests`（10）与 `WeakCacheTests`（7）共 33 个测试，全部通过。测试固定的是 API 表面与顺序规则，但刻意不断言 GC 驱逐（测试里的字符串键与短命条目在各自的测试期间都被钉住）—— 见 [GC行为与注意](../07_GC行为与注意/) 页。

**预期结果：** 对 `VeloxDev.Core.Test` 执行 `dotnet test` 会绿色通过 `WeakTypes` 测试。

## 2. 完整代码

一个自包含的控制台程序（目标 `net10.0`），跑遍四个类型。每个“死”的 `Payload`/处理器/键都在辅助方法内部创建，辅助方法返回后即不可达；随后 `ForceGc` 回收它们，控制台只报告存活项。所有 `using` 显式给出；唯一的外部依赖是对 `VeloxDev.Core` 的引用（见[安装依赖](../01_安装依赖/)页）：

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

## 3. 记录到的输出

下面是某次 `Release` 运行的控制台输出逐字转写（见运行声明）。它稳定，是因为每个死对象都在辅助方法内部创建，而辅助方法的栈帧在 GC 运行前就已返回：

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

## 4. 对照各页阅读输出

- `WeakQueue` / `WeakStack`：在填充辅助函数里创建的 `Payload(1)`/`Payload(3)`（队列）与 `Payload(10)`/`Payload(30)`（栈）已被回收，因此 `Count after GC: 1`，只有仍存活的 `alive` 项（`Value = 2`）被出队/出栈（[弱队列](../04_弱队列/)与[弱栈](../05_弱栈/)页，以及[GC行为与注意](../07_GC行为与注意/)页里的清扫规则）。
- `WeakDelegate`：以 `CanUpdateCache: false` 添加的死订阅者已被回收，因此第一次调用只触发 `liveSub`（`counter` 为 1）；`Clone()` 再从存活处理器重建，克隆调用把它抬到 2（[弱委托订阅](../03_弱委托订阅/)页）。
- `WeakCache`：死掉的 `Payload(200)` 键已被回收，所以对一个全新键 `TryGetCache` 返回 `False`，`ForeachCache` 只访问 `key1`（`key=100 value=value-100`）；随后 `Remove(key1)` 让查找变为 `False`（[弱缓存](../06_弱缓存/)页）。

## 5. 运行声明

- ✅ 已于 2026-09-07 实际构建并运行（`dotnet run -c Release`，目标 `net10.0`，项目引用本仓库的 `VeloxDev.Core`）。记录到的输出见第 3 节逐字转写；连续三次运行输出完全一致。同日还完整执行了 `WeakTypes` MSTest 套件（33/33 通过，见第 1 节）。
