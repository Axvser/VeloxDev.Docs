# 弱引用类型 — 快速开始

## 弱引用类型

### 快速开始

#### 1. 环境准备（Prerequisites）

- **支持目标**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK；已在 SDK 9.0/10.0 下验证 —— *被验证过*的环境。示例面向 `net9.0`。
- **包管理器：** NuGet / `dotnet` CLI。
- **所需服务：** 无 —— 四个弱集合类型位于 `VeloxDev.WeakTypes`，无运行时依赖。


#### 2. 安装 / 添加依赖

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 命令以 `0` 退出；`.csproj` 中出现 `<PackageReference Include="VeloxDev.Core" />` 并完成还原。四个类型在包的所有目标框架上都可用。

#### 3. 基础设置 / 注册

直接实例化集合类型即可 —— 没有注册步骤。唯一的契约是泛型约束：队列 / 栈元素与缓存键必须是引用类型（`class`），委托类型必须派生自 `System.Delegate`。

```csharp
using System;
using VeloxDev.WeakTypes;

var queue = new WeakQueue<Payload>();          // T : class
var stack = new WeakStack<Payload>();          // T : class
var changed = new WeakDelegate<Action<string>>();  // TDelegate : Delegate
var cache = new WeakCache<Payload, string>();  // TTargetKey : class, TCacheKey : class
```

**预期结果：** 四个对象无配置即可构造；集合存储 `WeakReference<T>`（缓存用 `ConditionalWeakTable`）而非强引用。

#### 4. 核心用法（分步进行）

**4.1 入队 / 压栈 / 添加处理器**

（`Payload`、`Subscriber` 与 `Counter` 是下方完整代码中定义的辅助类；`queue`、`stack` 与 `changed` 来自第 3 步。）

```csharp
queue.Enqueue(new Payload(1));      // 弱持有
var alive = new Payload(2);
queue.Enqueue(alive);               // 仍被引用 -> 不会被 GC 回收

stack.Push(new Payload(10));        // 弱持有

changed.AddHandler(liveSub.Handle); // 处理器被弱持有
```

**预期结果：** 仅被弱引用持有的条目可被回收；`alive` 与 `liveSub` 因你仍持有强引用而存活。

**4.2 强制执行 GC 并观察访问时清扫**

```csharp
ForceGc();
Console.WriteLine($"Count after GC: {queue.Count}");   // 先剪除死亡引用
if (queue.TryDequeue(out var item)) { }                // 跳过已回收条目
```

**预期结果：** `Count` 只反映存活条目；`TryDequeue` / `TryPop` / `TryPeek` 会跳过目标已被回收的条目。

**4.3 缓存增改读**

```csharp
cache.AddOrUpdate(key1, "value-100");
if (cache.TryGetCache(key1, out var v)) { }   // 摊还 O(1)
cache.ForeachCache((k, val) => Console.WriteLine($"{k} -> {val}"));
cache.Remove(key1);
```

**预期结果：** `TryGetCache` 对存活键返回对应值、对已回收键返回 `false`；`ForeachCache` 只遍历存活条目。

**4.4 `WeakDelegate` 调用与克隆**

```csharp
changed.Invoke(["hello"]);          // 对缓存的组合委托做 DynamicInvoke
var snapshot = changed.Clone();     // 仅从存活处理器重建
snapshot.Invoke(["world"]);
```

**预期结果：** 调用克隆只运行订阅者仍存活的处理器 —— 已回收订阅者的处理器在重建时被剪除。

#### 5. 验证

运行下方完整程序。一次示例运行（Release 构建，`net9.0`）输出：

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

**预期结果：** 只在辅助方法内创建的条目被 `ForceGc` 回收，因此队列 / 栈报告 `Count: 1` 且只出队 / 出栈存活条目；已回收的委托处理器与缓存键被跳过。

#### 6. 完整代码

```csharp
using System;
using VeloxDev.WeakTypes;

namespace WeakTypesQuickStart;

// 一个可被 GC 回收的简单引用类型条目。
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

    // 这里创建的条目在方法返回时离开作用域，因此只有弱引用还可达；下次 GC 会回收它们。
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
        // CanUpdateCache:false 避免立刻构建组合委托缓存，
        // 否则缓存会以强引用保住已死亡订阅者。
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

#### 7. 运行声明（Run Declaration）

- ✅ 已于 2026-08-17 实际构建并运行（`dotnet run -c Release`，目标 `net9.0`）。记录到的输出（见第 5 节）：`WeakQueue Count after GC: 1`、`Dequeued: 2`；`WeakStack Count after GC: 1`、`Popped: 2`；`WeakDelegate counter after GC + invoke: 1`、`counter after clone + invoke: 2`；`WeakCache TryGetCache(key1): True -> value-100`、`TryGetCache(new key): False`、`ForeachCache: key=100 value=value-100`、`TryGetCache(key1) after Remove: False`。
