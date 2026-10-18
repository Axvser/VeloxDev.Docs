# 弱引用类型 — 验证与完整代码

## 1. 用自动化测试验证

行为证据位于 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 的 MSTest 套件。仅运行弱引用类型测试（2026-10-01 对 `master` 的记录输出；2026-10-18 文档修订期间未重新运行）：

```text
总共 1 个测试文件与指定模式相匹配。
已通过! - 失败:     0，通过:    35，已跳过:     0，总计:    35，持续时间: 55 ms - VeloxDev.Core.Test.dll (net10.0)
```

这是在 `VeloxDev.Core.Test` 项目（目标 `net10.0`）上运行 `dotnet test --filter "FullyQualifiedName~WeakTypes"` 的结果：`WeakDelegateTests`（8）、`WeakQueueTests`（10）、`WeakStackTests`（10）与 `WeakCacheTests`（7）共 35 个测试全部通过。测试钉住 API 面与顺序规则，但有意不断言 GC 驱逐（测试中的字符串键与短命条目在每个测试期间保持 root）——见 GC 行为页。

**预期结果：** 在 `VeloxDev.Core.Test` 上运行 `dotnet test` 时，`WeakTypes` 测试全部通过。

## 2. 完整代码

一个自包含控制台程序（目标 `net10.0`），覆盖四个类型。每个“该死”的 `Payload`/处理器/键都在辅助方法内创建，因此辅助方法返回后它不可达；随后 `ForceGc` 回收它，控制台只报告幸存条目。所有 `using` 都显式写出；唯一外部要求是引用 `VeloxDev.Core`（见安装页）：

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

## 3. 记录输出

下面的记录是一次运行的逐字控制台输出（见运行声明）。它是稳定的，因为每个死对象都在辅助方法内创建，而该方法的帧在 GC 运行前已返回：

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

## 4. 对照页面读输出

- `WeakQueue` / `WeakStack`：在填充辅助方法中创建的 `Payload(1)`/`Payload(3)`（队列）与 `Payload(10)`/`Payload(30)`（栈）已被回收，因此 `Count after GC: 1`，且只有仍存活的 `alive` 条目（`Value = 2`）被出队/弹出（弱队列页、弱栈页，以及 GC 行为页的清扫规则）。
- `WeakDelegate`：以 `CanUpdateCache: false` 添加的死订阅者已被回收，因此第一次调用只触发 `liveSub`（`counter` 为 1）；随后 `Clone()` 从存活处理器重建，克隆的调用把它升到 2（弱委托页）。
- `WeakCache`：死掉的 `Payload(200)` 键已被回收，因此对一个全新键调用 `TryGetCache` 为 `False`，`ForeachCache` 只访问 `key1`（`key=100 value=value-100`）；随后 `Remove(key1)` 使查询变为 `False`（弱缓存页）。

## 5. 运行声明

- ⚠️ 2026-10-18 文档修订期间未重新运行——仅做静态核验。第 2 节的控制台程序曾在 2026-10-01 以 `dotnet run -c Debug` 构建并执行（目标 `net10.0`，对 `VeloxDev.Core` 使用项目引用）；第 3 节的记录就是那次运行的逐字输出，连续运行产生相同输出。`WeakTypes` MSTest 套件（35/35）也在同一天通过（第 1 节）。
- 当时运行的配置说明：`Release` 无法还原，因为 `VeloxDev.Core.Generator` 包引用被钉在 `10.0.0`，该版本当时尚未发布到 nuget.org（`NU1102`）。`Debug` 则使用本地生成器源码。弱引用类型源码本身与配置无关；若你今天复现示例，首选 `dotnet run -c Release`，而辅助方法中的生命周期安排使记录在两种配置下都保持稳定。
