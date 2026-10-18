# 验证与完整代码

## 运行控制台程序

下面的完整程序于 2026-10-18 用 .NET SDK 10.0.401 针对 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 构建并执行。

```csharp
using System;
using VeloxDev.AspectOriented;

namespace AopQuickStart;

public partial class Counter
{
    [AspectOriented]
    public int Total { get; set; }

    [AspectOriented]
    public int Add(int a, int b)
    {
        Total = a + b;
        return Total;
    }

    [AspectOriented]
    public void Reset()
    {
        Total = 0;
    }
}

public static class Program
{
    public static void Main()
    {
        var counter = new Counter();
        var proxy = counter.Aop();

        proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add),
            (parameters, previous) =>
            {
                Console.WriteLine($"[start] Add({parameters?[0]}, {parameters?[1]}) called");
                return null;
            },
            (parameters, previous) =>
            {
                Console.WriteLine("[coverage] original Add() body is skipped");
                return (object?)((int)(parameters?[0] ?? 0) + (int)(parameters?[1] ?? 0));
            },
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Add() returned {previous}");
                return null;
            });

        proxy.SetProxy(ProxyMembers.Setter, nameof(Counter.Total),
            null,
            null,
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Total set to {parameters?[0]}");
                return null;
            });

        proxy.SetProxy(ProxyMembers.Getter, nameof(Counter.Total),
            (parameters, previous) =>
            {
                Console.WriteLine("[start] Total getter read");
                return null;
            },
            null,
            null);

        int result = proxy.Add(2, 3);
        Console.WriteLine($"result = {result}");

        proxy.Total = 42;
        int total = proxy.Total;
        Console.WriteLine($"total = {total}");

        proxy.Reset();
        Console.WriteLine($"after Reset, total = {proxy.Total}");

        var original = Aop.GetTarget<Counter>(proxy);
        Console.WriteLine($"original.Total = {original?.Total}");
    }
}
```

**预期结果：** 程序按顺序输出：

```text
[start] Add(2, 3) called
[coverage] original Add() body is skipped
[end] Add() returned 5
result = 5
[end] Total set to 42
[start] Total getter read
total = 42
[start] Total getter read
after Reset, total = 0
original.Total = 0
```

`Add` 返回 `5` 是因为 `coverage` 替换了成员体：`Total = a + b` 从未运行，`end` 收到的是 `coverage` 的结果。`Reset` 没有钩子，因此直接调用目标并把 `Total` 置为 `0`；随后的读取仍会触发 getter 的 `start`。

## 操作随仓库的 Demo

`Examples/AOP/WPF/Demo`（`net9.0-windows`）在 `MainWindow.ConfigureAOP` 中为 `TeamViewModel` 注册了同样的三种角色：

| 按钮 | 动作 | 触发的钩子 | 消息 |
|---|---|---|---|
| `Click2` | 读 `Name` | getter `start` | `a read operation happened at [...]` |
| `Click3` | 写 `Name` | setter `end` | `the name of team has been changed to [...]` |
| `Click4` | 调 `Reset()` | method `coverage` | `the default Reset() has been cancelled` |
| `Click1` | 添加成员 | `AOP_OnMemberAdded` 的 `end` | `a member named [Jack] has been added` |
| `Click0` | 移除成员 | `AOP_OnMemberRemoved` 的 `end` | `a member named [...] has been removed` |

集合按钮走的是事件路径：`TeamViewModel` 订阅 `CollectionChanged` 并转发给 `this.Aop().AOP_OnMemberAdded(sender, e)`，所以通知会重新进入同一个缓存代理，`[AspectOriented]` 方法与直接调用一样被拦截。

**预期结果：** 每个按钮只显示表中对应的消息；`Click4` 之后团队状态不变，因为 `coverage` 取消了 `Reset()`。

## 运行声明

- ✅ **2026-10-18 实际执行**，SDK 10.0.401：
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~AspectOriented"` → `已通过! - 失败: 0，通过: 13，已跳过: 0，总计: 13，持续时间: 49 ms`。
    - `dotnet build Examples/AOP/WPF/Demo/Demo.csproj -c Debug` → `已成功生成。 0 个警告 0 个错误`。
    - `dotnet build Examples/AOP/Avalonia/Demo/Demo.csproj -c Debug` → `已成功生成。 0 个警告 0 个错误`。
    - 上述控制台程序在引用 `Src/Core/VeloxDev.Core` 与生成器分析器的临时 `net10.0` 工程中构建运行，逐字产生上面十行输出。
- ⚠️ 两个 GUI Demo **只构建、未交互点击**；其消息预期来自 `MainWindow.xaml.cs` 与 `MainWindow.xaml` 的按钮接线。
