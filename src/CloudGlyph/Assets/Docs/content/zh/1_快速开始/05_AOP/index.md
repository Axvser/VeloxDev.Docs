# AOP — 快速入门

## AOP

### 快速入门

`VeloxDev.Core` 的 AOP（面向切面编程）功能会在运行时拦截 `partial` 类中被 `[AspectOriented]` 标记的成员调用，底层是在编译期生成的 `DispatchProxy`。每个目标实例只创建一次代理并缓存在弱表中，通过代理你可以为属性的 getter、setter 以及方法挂载 `start` / `coverage` / `end` 三种钩子。

> AOP 运行时只针对包的 `net5.0+` 目标编译（所有运行时源文件都包裹在 `#if NET` 中）。它在 `VeloxDev.Core` 的 `netstandard2.0` / `netframework4.6.1` 目标上**不可用**。

#### 1. 前置条件

- **支持目标：** AOP 运行时为 `#if NET`（见 `VeloxDev.Core.csproj`）—— 使用方项目必须面向 .NET（Core）5.0+ 的 TFM（不能用 .NET Framework）；核心包本身也多目标 `netstandard2.0` / `netframework4.6.1`。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK 以运行 AOP 源码生成器；示例面向 `net9.0` / `net9.0-windows` —— *被验证过*的配置。
- **包管理器：** NuGet / dotnet CLI。
- **所需服务：** 无。


#### 2. 安装 / 添加依赖

添加 `VeloxDev.Core` NuGet 包：

```bash
dotnet add package VeloxDev.Core --version 7.0.0
```

该包包含运行时（`VeloxDev.AspectOriented`），并依赖源生成器 `VeloxDev.Core.Generator`，后者在编译期生成代理接口和 `Aop()` 扩展方法。

**预期结果：** `.csproj` 中出现对 `VeloxDev.Core`（并间接引入 `VeloxDev.Core.Generator`）的 `PackageReference`；命令以退出码 0 结束。

#### 3. 基础设置 / 注册

声明一个 `partial class`，并用 `[AspectOriented]` 标记你想要拦截的成员：

```csharp
using VeloxDev.AspectOriented;

namespace AopDemo;

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
}
```

生成器（`AopProxy` / `AopInterface`）会产出两个产物：

- 代理接口 `VeloxDev.AopInterfaces.Counter_AopDemo_Aop : IAspectOriented`，声明每个 `[AspectOriented]` 成员（`Total` 与 `Add`）；`partial` 类会被扩展为实现该接口；
- 带缓存的扩展方法 `public static Counter_AopDemo_Aop Aop(this Counter instance)`（命名空间 `VeloxDev.AspectOriented`）。

**预期结果：** `dotnet build` 成功；调用 `instance.Aop()` 返回一个实现所生成接口的代理。

#### 4. 核心用法（逐步）

1) **获取代理** — `var proxy = counter.Aop();`

   **预期结果：** `proxy` 是实现了 `Counter_AopDemo_Aop` 的 `DispatchProxy`；再次调用 `Aop()` 返回同一个缓存的代理实例（通过 `AopCache.Resolve` 存在每对类型的 `ConditionalWeakTable` 中）。

2) **挂载钩子** — 为某个成员注册 `(start, coverage, end)` 三元组：

   ```csharp
   proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add), start, coverage, end);
   ```

   **预期结果：** 三元组被写入 `ProxyInstance` 的方法钩子表（`MethodActions`）。`coverage` 非空时替换原逻辑；`coverage` 为 `null` 时代理回退为对真实目标做反射调用。

3) **通过代理调用成员** — `int result = proxy.Add(2, 3);`

   **预期结果：** 调用汇入 `ProxyInstance.Invoke`，它按方法名分发并执行钩子。

4) **观察钩子顺序** — 对同时挂载了三个钩子的成员，顺序为：`start` → `coverage`（当 `coverage == null` 时为反射回退）→ `end`。`start` 与 `coverage` 可通过 `ProxyHandler` 的 `previous` 参数串联返回值；`coverage`（或反射）的结果返回给调用方。

   **预期结果：** 使用步骤 2 的钩子，控制台依次打印 `[start] ...`、`[coverage] ...`、`[end] ...`，然后是 `result = 5`。

5) **反向映射** — `var original = Aop.GetTarget<Counter>(proxy);`

   **预期结果：** `original` 是创建该代理的原始 `Counter` 实例（由生成的 `Aop()` 扩展通过 `Aop.Map` 注册的映射）。

#### 5. 验证

运行随附的任一 demo —— `Examples/AOP/WPF/Demo`（WPF）或 `Examples/AOP/Avalonia/Demo`（Avalonia）——或步骤 6 中的控制台程序，确认钩子顺序：

- 读取 `Name` 触发 getter **start** 钩子；
- 写入 `Name` 触发 setter **end** 钩子；
- 调用 `Reset()` 触发**取消默认逻辑**的 **coverage** 钩子；
- 添加 / 移除成员触发 `AOP_OnMemberAdded` / `AOP_OnMemberRemoved` 的 **end** 钩子。

在 WPF demo 中由按钮 `Click0`..`Click4` 驱动，以 `MessageBox` 弹窗呈现；Avalonia demo 使用 toast `Notification`。

#### 6. 完整代码

一个自包含的控制台程序。创建一个 `net9.0` 控制台项目，添加 `VeloxDev.Core`，并把 `Program.cs` 替换为：

```csharp
using System;
using VeloxDev.AspectOriented;

namespace AopDemo;

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
}

public static class Program
{
    public static void Main()
    {
        var counter = new Counter();
        var proxy = counter.Aop();

        // 一次 SetProxy 调用即可注册整个 (start, coverage, end) 三元组。
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

        // 反射回退路径：coverage 为 null，仅挂 end 钩子。
        proxy.SetProxy(ProxyMembers.Setter, nameof(Counter.Total),
            null,
            null,
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Total set to {parameters?[0]} (reflection ran the real setter)");
                return null;
            });

        // Getter start 钩子。
        proxy.SetProxy(ProxyMembers.Getter, nameof(Counter.Total),
            (parameters, previous) =>
            {
                Console.WriteLine("[start] Total getter called");
                return null;
            },
            null,
            null);

        int result = proxy.Add(2, 3);
        Console.WriteLine($"result = {result}");

        proxy.Total = 42;
        int total = proxy.Total;
        Console.WriteLine($"total = {total}");

        var original = Aop.GetTarget<Counter>(proxy);
        Console.WriteLine($"original.Total = {original?.Total}");
    }
}
```

所有符号自洽：`Counter`、`Total`、`Add`、`proxy`、`result`、`total`、`original` 均已在上面定义；生成的 `Counter_AopDemo_Aop` 接口与 `Aop()` 扩展由源生成器根据 `[AspectOriented]` 成员产出。

**预期控制台输出（静态推导，非实际运行记录）：**

```text
[start] Add(2, 3) called
[coverage] original Add() body is skipped
[end] Add() returned 5
result = 5
[end] Total set to 42 (reflection ran the real setter)
[start] Total getter called
total = 42
original.Total = 42
```

#### 7. 运行声明

- ⚠️ 未实际运行 — 仅做了静态验证。本会话读取了 `Examples/AOP/WPF/Demo` 与 `Examples/AOP/Avalonia/Demo` 的 demo 源码作为证据，但并未编译并运行任何调用 AOP 代理的控制台 / WPF / Avalonia 工程，因此上面的控制台输出是静态推导而非实际录制的结果。
