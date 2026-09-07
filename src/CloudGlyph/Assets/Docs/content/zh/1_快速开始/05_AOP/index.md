# AOP — 快速开始

## AOP

### 快速开始

`VeloxDev.Core` 的 **aop** 功能为 `partial class` 提供运行时面向切面拦截：用 `[AspectOriented]` 标记公开成员后，Roslyn 源生成器会生成一个代理接口和一个 `Aop()` 扩展；调用该扩展会得到一个 `DispatchProxy`，此后每个 `[AspectOriented]` 成员的调用都可以被挂上钩子。对每个成员，你可以挂上由 `ProxyHandler` 委托构成的 `(start, coverage, end)` 三元组：

- `start` 在成员执行前运行；
- `coverage` 非空时替换真实逻辑（其结果作为返回值）；为 `null` 时代理回退为对目标做反射调用以执行真实成员；
- `end` 在成员执行后运行，通过 `previous` 拿到将被返回的值。

该功能是纯粹的 `VeloxDev.Core` + 源生成器特性——**不需要**任何平台适配器包，无论你的应用是 WPF、Avalonia、WinUI、MAUI、WinForms 还是 Razor。

> 整个 AOP 运行时（`Src/Core/VeloxDev.Core/AspectOriented/` 与 `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/` 下的每个文件）都包裹在 `#if NET` 中，因此它只存在于包的 `net5.0` 构建里。它**不会**被编译进 `netstandard2.0`、`netframework4.6.1` 或 `netcoreapp3.0` 目标。

#### 1. 前置条件

- **支持目标**（来自使用方工程）：面向 .NET 5.0+ 的 TFM（`net5.0`、`net6.0`、`net7.0`、`net8.0`、`net9.0`、`net10.0`、…）。`VeloxDev.Core.csproj` 多目标 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`，但 `#if NET` 的 AOP 运行时只在 `net5.0` 产物中。面向 .NET Framework / `netcoreapp3.0` / 仅 netstandard 的使用方无法使用该功能。
- **SDK / 运行时：** 能编译 `net5.0+` 且自带源生成器所需 Roslyn 编译器的 .NET SDK（生成器要求 `Microsoft.CodeAnalysis.CSharp` ≥ 4.3.1，即 .NET SDK 6.0.4xx / VS 2022 17.3+ 即可）。已在 SDK 9.0/10.0 上验证——这是*被验证过*的环境。下面的示例面向 `net9.0`。
- **包管理器：** NuGet / `dotnet` CLI。
- **所需服务：** 无。不需要任何平台适配器包。

#### 2. 安装 / 添加依赖

添加 `VeloxDev.Core` 包（它以依赖形式携带 `VeloxDev.Core.Generator` 分析器，因此代理源生成器会自动对工程生效）：

```bash
dotnet add package VeloxDev.Core
```

或者在本仓库内改用工程引用——随附示例是从其所在目录（位于 `Examples/AOP/…` 下）向上四级引用核心工程：

```bash
dotnet add reference ..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj
```

**预期结果：** 命令以退出码 0 结束；`.csproj` 中出现 `PackageReference`（或 `ProjectReference`）且还原完成。此后构建工程即会运行 AOP 生成器（`VeloxDev.Generators.AopInterface` 与 `VeloxDev.Generators.AopProxy`，程序集 `VeloxDev.Core.Generator`）。

#### 3. 基础设置 / 注册

声明一个**位于命名空间中的 `partial` 类**——生成器会产出第二个 `partial` 声明使类实现生成的代理接口，所以声明必须是 `partial`。用 `[AspectOriented]` 标记你想拦截的每个公开成员：

```csharp
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
}
```

该特性可应用在：

- **方法** — 每个 `public [AspectOriented]` 方法都会被加入代理接口；
- **属性** — 把 `[AspectOriented]` 直接放在显式自动属性上，或与一个属性生成特性一起放在后备字段上。随附示例使用后一种路径：`[VeloxProperty][AspectOriented] private string _name = string.Empty;` 既把 `_name` 变成可观察的 `Name` 属性，又把 `Name { get; set; }` 加入代理接口。（`VeloxProperty` 是独立的 **mvvm** 功能的特性，命名空间 `VeloxDev.MVVM`。）

对于上面的 `Counter`，生成器会产出三个产物：

- **接口** `VeloxDev.AopInterfaces.Counter_AopQuickStart_Aop : VeloxDev.AspectOriented.IAspectOriented` — 声明 `Total` 与 `Add`；
- **partial 类** `Counter_AopQuickStart_AOP.g.cs` — `partial class Counter : …Counter_AopQuickStart_Aop`，与你的声明合并，使类实现该接口；
- **扩展** `Counter_AopQuickStart_AopExtensions`（命名空间 `VeloxDev.AspectOriented`）— `public static Counter_AopQuickStart_Aop Aop(this Counter instance)`，通过 `AopCache.Resolve<Counter, Counter_AopQuickStart_Aop>` 取（或建）缓存的代理，并用 `ProxyEx.CreateProxy<…>` 创建、用 `Aop.Map` 注册反向映射。

**预期结果：** `dotnet build` 成功；`instance.Aop()` 返回实现了所生成接口的代理，对同一实例再次调用返回*同一个*缓存代理。

#### 4. 核心用法（逐步）

**4.1 获取代理**

```csharp
var proxy = counter.Aop();
```

**预期结果：** `proxy` 是一个以所生成接口为类型的 `DispatchProxy`（`ProxyInstance`）。再次 `counter.Aop()` 返回同一个缓存实例；不同的 `Counter` 实例得到各自的代理。

**4.2 为成员挂载钩子三元组**

`SetProxy` 是作用在代理上的扩展方法（`ProxyMembers.Method` / `.Getter` / `.Setter` + 成员名 + `(start, coverage, end)` 三元组）：

```csharp
proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add),
    (parameters, previous) =>
    {
        Console.WriteLine($"[start] Add({parameters?[0]}, {parameters?[1]})");
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
```

`coverage` 为 `null` 时成员照常真实执行（代理对目标类型做反射）；`coverage` 非空时替换该逻辑，其返回值即成员的返回值。

**预期结果：** 三元组被存入该 `ProxyInstance` 的按成员动作表；这些 lambda 都可转换为委托 `ProxyHandler`（即 `object? ProxyHandler(object?[]? parameters, object? previous)`）。

**4.3 通过代理调用成员**

```csharp
int result = proxy.Add(2, 3);
```

**预期结果：** 调用汇入 `ProxyInstance.Invoke`，它按反射到的成员名（`Add`、`get_Total`、`set_Total`、…）分发并执行钩子。`result` 为 `5`。

**4.4 观察钩子顺序与返回值链路**

对同时挂载三个钩子的成员，顺序为：`start` → `coverage`（`coverage == null` 时改为反射执行真实成员）→ `end`。`start` 以 `previous == null` 运行；其返回值作为 `previous` 传给 `coverage`；`end` 以即将返回的值作为 `previous`。调用方最终收到的是该值（coverage 结果或反射调用的结果）。

**预期结果：** 控制台依次打印 `[start] …`、`[coverage] …`、`[end] …`，然后是 `result = 5`。

**4.5 反向映射：由代理找回目标**

```csharp
var original = Aop.GetTarget<Counter>(proxy);
```

**预期结果：** `original` 正是创建该代理的那个 `Counter` 实例。该映射由 `Aop()` 扩展在构建代理时通过 `Aop.Map` 注册。

**生命周期说明：** AOP 不提供取消或按代理释放的 API。代理一旦创建，`ProxyEx.CreateProxy` 会把它登记进静态表 `ProxyInstance.ProxyIDs` / `ProxyInstances`，且 `AopCache.Resolve` 会按目标实例缓存它，因此已创建的代理及其已注册钩子会存活到进程结束。

#### 5. 验证

运行随附的任一 demo —— `Examples/AOP/WPF/Demo`（WPF，`net9.0-windows`，以 `MessageBox` 弹窗提示）或 `Examples/AOP/Avalonia/Demo`（Avalonia，`net9.0`，以 toast `Notification` 提示）——并依次触发五个按钮确认钩子：

| 按钮 | 动作 | 触发的钩子 | 消息 |
|---|---|---|---|
| `Click2` | 读取 `Name` | getter `start` | `a read operation happened at [...]` |
| `Click3` | 写入 `Name` | setter `end` | `the name of team has been changed to [...]` |
| `Click4` | 调用 `Reset()` | method `coverage`（取消默认逻辑） | `the default Reset() has been cancelled` |
| `Click1` | `Members.Add(new MemberViewModel { Name = "Jack" })` | `AOP_OnMemberAdded` end | `a member named [Jack] has been added` |
| `Click0` | `Members.RemoveAt(0)` | `AOP_OnMemberRemoved` end | `a member named [...] has been removed` |

集合按钮之所以生效，是因为 demo 会重新进入自己的代理：`TeamViewModel` 在构造函数中订阅 `CollectionChanged` 并转发给 `this.Aop().AOP_OnMemberAdded(sender, e)` / `AOP_OnMemberRemoved(sender, e)`，于是添加/移除流程本身也是一次被拦截的 `[AspectOriented]` 方法调用。也可以改为运行第 6 步的控制台程序。

**预期结果：** 每次交互都弹出对应消息；`Reset()` 弹出取消提示且团队状态*并未*被重置。

#### 6. 完整代码

创建一个 `net9.0` 控制台工程，添加 `VeloxDev.Core`（或引用 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`），并把 `Program.cs` 替换为：

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

        // Add 上的 start + coverage + end：coverage 替换真实方法体。
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

        // Total 的 setter end 钩子：coverage 为 null，反射执行真实 setter。
        proxy.SetProxy(ProxyMembers.Setter, nameof(Counter.Total),
            null,
            null,
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Total set to {parameters?[0]}");
                return null;
            });

        // Total 的 getter start 钩子。
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

所有符号自洽：`Counter`、`Total`、`Add`、`Reset`、`counter`、`proxy`、`result`、`total` 与 `original` 均已在上面定义；生成的 `Counter_AopQuickStart_Aop` 接口、`partial class Counter` 合并与 `Aop()` 扩展由编译器根据 `[AspectOriented]` 成员产出。

**预期控制台输出（静态推导，非实际运行记录）：**

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

#### 7. 运行声明

- ⚠️ 未实际运行 — 仅做了静态验证。本会话完整阅读了 `Examples/AOP/{WPF,Avalonia}/Demo` 下的 WPF 与 Avalonia demo 作为证据（其 `bin/` 产物表明此前构建成功），并把上面的控制台程序与运行时（`Src/Core/VeloxDev.Core/AspectOriented/*.cs`）及生成器（`Src/Generators/VeloxDev.Core.Generator/AopInterface.cs`、`AopProxy.cs`）源码逐一对照，但并未在本会话中编译并运行任何调用 AOP 代理的控制台工程，因此上面的控制台输出是静态推导而非实际录制的结果。
