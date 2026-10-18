# Verify and Complete Code

## Run the console program

The complete program below was built and executed with .NET SDK 10.0.401 on 2026-10-18 against `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`.

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

**Expected result:** the program prints, in order:

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

`Add` returns `5` because `coverage` replaced the body: the member's own `Total = a + b` never ran, so the `end` stage received the `coverage` result. `Reset` has no hooks, so it calls the target directly and sets `Total` to `0`; the following read still fires the getter's `start`.

## Exercise the shipped demo

`Examples/AOP/WPF/Demo` (`net9.0-windows`) registers the same three roles on `TeamViewModel` in `MainWindow.ConfigureAOP`:

| Button | Action | Hook | Message |
|---|---|---|---|
| `Click2` | read `Name` | getter `start` | `a read operation happened at [...]` |
| `Click3` | write `Name` | setter `end` | `the name of team has been changed to [...]` |
| `Click4` | call `Reset()` | method `coverage` | `the default Reset() has been cancelled` |
| `Click1` | add a member | `AOP_OnMemberAdded` `end` | `a member named [Jack] has been added` |
| `Click0` | remove a member | `AOP_OnMemberRemoved` `end` | `a member named [...] has been removed` |

The collection buttons work through an event: `TeamViewModel` subscribes to `CollectionChanged` and forwards to `this.Aop().AOP_OnMemberAdded(sender, e)`, so the notification re-enters the same cached proxy and the `[AspectOriented]` method is intercepted like any direct call.

**Expected result:** each button shows exactly the message in the table; after `Click4` the team state is unchanged because `coverage` cancelled `Reset()`.

## Run Declaration

- ✅ **Executed on 2026-10-18**, SDK 10.0.401:
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~AspectOriented"` → `已通过! - 失败: 0，通过: 13，已跳过: 0，总计: 13，持续时间: 49 ms`.
    - `dotnet build Examples/AOP/WPF/Demo/Demo.csproj -c Debug` → `已成功生成。 0 个警告 0 个错误`.
    - `dotnet build Examples/AOP/Avalonia/Demo/Demo.csproj -c Debug` → `已成功生成。 0 个警告 0 个错误`.
    - The console program above, built in a temporary `net10.0` project referencing `Src/Core/VeloxDev.Core` plus the generator analyzer, produced the ten output lines shown above verbatim.
- ⚠️ The two GUI demos were **built but not interactively clicked**; their message expectations come from `MainWindow.xaml.cs` and the button-to-handler wiring in `MainWindow.xaml`.
