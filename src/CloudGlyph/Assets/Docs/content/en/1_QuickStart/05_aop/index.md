# AOP — Quick Start

The **aop** feature of `VeloxDev.Core` gives you runtime aspect-oriented interception for a `partial class`: mark a public member with `[AspectOriented]` and a Roslyn source generator emits a proxy interface plus an `Aop()` extension; calling the extension returns a `DispatchProxy` through which every `[AspectOriented]` member call can be hooked. For each member you attach an optional `(start, coverage, end)` triple of `ProxyHandler` delegates:

- `start` runs before the member;
- `coverage`, when non-null, replaces the real logic (its result is returned); when null the proxy falls back to invoking the real member on the target by reflection;
- `end` runs after, receiving the produced value as `previous`.

The feature is a pure `VeloxDev.Core` + source-generator feature — it needs **no** platform adapter package, regardless of whether your app is WPF, Avalonia, WinUI, MAUI, WinForms or Razor.

> The whole AOP runtime (every file under `Src/Core/VeloxDev.Core/AspectOriented/` and `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/`) is wrapped in `#if NET`, so it exists only in the `net5.0` build of the package. It is **not** compiled into the `netstandard2.0`, `netframework4.6.1` or `netcoreapp3.0` assets.

## 1. Prerequisites

- **Supported target** (from the consuming project): a .NET 5.0+ TFM (`net5.0`, `net6.0`, `net7.0`, `net8.0`, `net9.0`, `net10.0`, …). `VeloxDev.Core.csproj` multi-targets `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`, but the `#if NET` AOP runtime is only inside the `net5.0` asset. A .NET Framework / `netcoreapp3.0` / netstandard-only consumer cannot use the feature.
- **SDK / runtime:** a .NET SDK that can compile `net5.0+` and ships the Roslyn compiler the source generator needs (generator requires `Microsoft.CodeAnalysis.CSharp` ≥ 4.3.1, i.e. any .NET SDK 6.0.4xx / VS 2022 17.3+). Verified against SDK 9.0/10.0 — the *tested* environment. The example below targets `net9.0`.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:** none. No platform-adapter package is needed.

## 2. Install / Add Dependency

Add the `VeloxDev.Core` package (it carries the `VeloxDev.Core.Generator` analyzer as a dependency, so the proxy source generator is available to your project automatically):

```bash
dotnet add package VeloxDev.Core
```

Or, when working inside this repository, add a project reference instead — the shipped demos reference the core project from four levels up (their folder sits under `Examples/AOP/…`):

```bash
dotnet add reference ..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj
```

**Expected result:** the command exits `0`; a `PackageReference` (or `ProjectReference`) appears in the `.csproj` and restore completes. From here on, building the project also runs the AOP generators (`VeloxDev.Generators.AopInterface` and `VeloxDev.Generators.AopProxy`, in assembly `VeloxDev.Core.Generator`).

## 3. Basic Setup / Registration

Declare a **`partial` class in a namespace** — the generators emit a second `partial` part that makes the class implement the generated proxy interface, so the declaration must be `partial`. Mark every public member you want to intercept with `[AspectOriented]`:

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

The attribute may be applied to:

- **methods** — every `public [AspectOriented]` method is added to the proxy interface;
- **properties** — put `[AspectOriented]` directly on an explicit auto-property, or pair it with a property-generating attribute on the backing field. The shipped demos use the latter route: `[VeloxProperty][AspectOriented] private string _name = string.Empty;` turns `_name` into the observable `Name` property *and* adds `Name { get; set; }` to the proxy interface. (`VeloxProperty` is the attribute of the separate **mvvm** feature, namespace `VeloxDev.MVVM`.)

For `Counter` above the generators produce three artifacts:

- **Interface** `VeloxDev.AopInterfaces.Counter_AopQuickStart_Aop : VeloxDev.AspectOriented.IAspectOriented` — declares `Total` and `Add`;
- **Partial class** `Counter_AopQuickStart_AOP.g.cs` — `partial class Counter : …Counter_AopQuickStart_Aop`, which merges with your declaration so the class implements the interface;
- **Extension** `Counter_AopQuickStart_AopExtensions` in namespace `VeloxDev.AspectOriented` — `public static Counter_AopQuickStart_Aop Aop(this Counter instance)`, which resolves (get-or-create) a cached proxy through `AopCache.Resolve<Counter, Counter_AopQuickStart_Aop>`, creating it with `ProxyEx.CreateProxy<…>` and registering the reverse map with `Aop.Map`.

**Expected result:** `dotnet build` succeeds; `instance.Aop()` returns a proxy that implements the generated interface, and calling it again for the same instance returns the *same* cached proxy instance.

## 4. Core Usage (Step by Step)

**4.1 Get the proxy**

```csharp
var proxy = counter.Aop();
```

**Expected result:** `proxy` is a `DispatchProxy` (`ProxyInstance`) typed as the generated interface. A second `counter.Aop()` returns the same cached instance; a different `Counter` gets its own proxy.

**4.2 Attach a hook triple to a member**

`SetProxy` is an extension on the proxy (`ProxyMembers.Method`, `.Getter` or `.Setter`, plus the member name and the `(start, coverage, end)` triple):

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

A `null` `coverage` leaves the member to run for real (the proxy reflects over the target type); a non-null `coverage` replaces that logic and its return value becomes the member's result.

**Expected result:** the triple is stored in the per-member action table of the `ProxyInstance`; the handlers are lambdas convertible to `ProxyHandler`, which is `object? ProxyHandler(object?[]? parameters, object? previous)`.

**4.3 Call the member through the proxy**

```csharp
int result = proxy.Add(2, 3);
```

**Expected result:** the call funnels into `ProxyInstance.Invoke`, which dispatches on the reflected member name (`Add`, `get_Total`, `set_Total`, …) and runs the hooks. `result` is `5`.

**4.4 Observe the hook order and return-value chain**

For a member with all three hooks the order is: `start` → `coverage` (or the real member by reflection when `coverage == null`) → `end`. `start` runs with `previous == null`; its return value is passed to `coverage` as `previous`; `end` receives the value that is about to be returned as `previous`. That value (coverage result, or the reflected call's result) is what the caller receives.

**Expected result:** the console prints, in order, `[start] …`, `[coverage] …`, `[end] …`, then `result = 5`.

**4.5 Reverse-map the proxy to its target**

```csharp
var original = Aop.GetTarget<Counter>(proxy);
```

**Expected result:** `original` is the exact `Counter` instance the proxy was created for. The mapping was stored by `Aop.Map` when the `Aop()` extension built the proxy.

**Lifecycle note:** AOP exposes no cancellation or per-proxy disposal. Once a proxy exists, `ProxyEx.CreateProxy` keeps it registered in the static `ProxyInstance.ProxyIDs` / `ProxyInstances` tables and `AopCache.Resolve` caches it per target, so created proxies and their registered hooks persist for the lifetime of the process.

## 5. Verification

Run one of the shipped demos — `Examples/AOP/WPF/Demo` (WPF, `net9.0-windows`, alerts via `MessageBox`) or `Examples/AOP/Avalonia/Demo` (Avalonia, `net9.0`, alerts via toast `Notification`s) — and exercise the five buttons to confirm the hooks:

| Button | Action | Hook that fires | Message |
|---|---|---|---|
| `Click2` | read `Name` | getter `start` | `a read operation happened at [...]` |
| `Click3` | write `Name` | setter `end` | `the name of team has been changed to [...]` |
| `Click4` | call `Reset()` | method `coverage` (cancels default logic) | `the default Reset() has been cancelled` |
| `Click1` | `Members.Add(new MemberViewModel { Name = "Jack" })` | `AOP_OnMemberAdded` end | `a member named [Jack] has been added` |
| `Click0` | `Members.RemoveAt(0)` | `AOP_OnMemberRemoved` end | `a member named [...] has been removed` |

The collection buttons work because the demo re-enters its own proxy: `TeamViewModel` subscribes to `CollectionChanged` in its constructor and forwards to `this.Aop().AOP_OnMemberAdded(sender, e)` / `AOP_OnMemberRemoved(sender, e)`, so the add/remove flow is itself an intercepted `[AspectOriented]` method call. Alternatively, run the console program in step 6.

**Expected result:** every interaction shows the corresponding message; `Reset()` shows the cancellation message and the team state is *not* reset.

## 6. Complete Code

Create a `net9.0` console project, add `VeloxDev.Core` (or reference `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`), and replace `Program.cs`:

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

        // start + coverage + end on Add: coverage replaces the real body.
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

        // Setter end hook on Total: coverage is null, reflection runs the real setter.
        proxy.SetProxy(ProxyMembers.Setter, nameof(Counter.Total),
            null,
            null,
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Total set to {parameters?[0]}");
                return null;
            });

        // Getter start hook on Total.
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

Every symbol is self-consistent: `Counter`, `Total`, `Add`, `Reset`, `counter`, `proxy`, `result`, `total` and `original` are all defined above; the generated `Counter_AopQuickStart_Aop` interface, the `partial class Counter` merge and the `Aop()` extension are produced from the `[AspectOriented]` members at compile time.

**Expected console output (statically derived, not recorded from a run):**

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

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only. The WPF and Avalonia demos under `Examples/AOP/{WPF,Avalonia}/Demo` were read in full as evidence (their `bin/` artifacts show successful prior builds), and the console program above was cross-checked against the runtime (`Src/Core/VeloxDev.Core/AspectOriented/*.cs`) and generator (`Src/Generators/VeloxDev.Core.Generator/AopInterface.cs`, `AopProxy.cs`) sources, but no console project exercising the AOP proxy was compiled and executed in this session, so the console output above is a static derivation rather than a recorded transcript.
