# AOP — Quick Start

## AOP

### Quick Start

The AOP (aspect-oriented programming) feature of `VeloxDev.Core` intercepts calls to `[AspectOriented]` members of a `partial` class at runtime, using a `DispatchProxy` generated at compile time. A proxy is created once per target instance, cached in a weak table, and lets you attach `start` / `coverage` / `end` hooks to property getters, property setters, and methods.

> The AOP runtime is compiled only for the `net5.0+` targets of the package (every runtime source file is wrapped in `#if NET`). It is **not** available on the `netstandard2.0` / `netframework4.6.1` targets of `VeloxDev.Core`.

#### 1. Prerequisites

- **Supported targets:** the AOP runtime is `#if NET` (see `VeloxDev.Core.csproj`) — the consuming project must target a .NET (Core) 5.0+ TFM (not .NET Framework); the core package itself also multi-targets `netstandard2.0` / `netframework4.6.1`.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+) for the AOP source generator; the demos target `net9.0` / `net9.0-windows` — *tested* configurations.
- **Package manager:** NuGet / dotnet CLI.
- **Required services:** none.


#### 2. Install / Add Dependency

Add the `VeloxDev.Core` NuGet package:

```bash
dotnet add package VeloxDev.Core --version 7.0.0
```

The package contains the runtime (`VeloxDev.AspectOriented`) and depends on the source generator `VeloxDev.Core.Generator`, which emits the AOP interface and the `Aop()` extension at compile time.

**Expected result:** a `PackageReference` to `VeloxDev.Core` (and, transitively, `VeloxDev.Core.Generator`) appears in the `.csproj`; the command exits with code 0.

#### 3. Basic Setup / Registration

Declare a `partial class` and mark the members you want to intercept with `[AspectOriented]`:

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

The generator (`AopProxy` / `AopInterface`) emits two artifacts:

- the proxy interface `VeloxDev.AopInterfaces.Counter_AopDemo_Aop : IAspectOriented`, declaring every `[AspectOriented]` member (`Total` and `Add`); the `partial` class is extended to implement it, and
- the cached extension `public static Counter_AopDemo_Aop Aop(this Counter instance)` in namespace `VeloxDev.AspectOriented`.

**Expected result:** `dotnet build` succeeds; calling `instance.Aop()` returns a proxy that implements the generated interface.

#### 4. Core Usage (Step by Step)

1) **Get the proxy** — `var proxy = counter.Aop();`

   **Expected result:** `proxy` is a `DispatchProxy` implementing `Counter_AopDemo_Aop`; calling `Aop()` a second time returns the same cached proxy instance (stored in a per-pair `ConditionalWeakTable` via `AopCache.Resolve`).

2) **Attach hooks** — register a `(start, coverage, end)` triple for a member:

   ```csharp
   proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add), start, coverage, end);
   ```

   **Expected result:** the triple is stored in the method hook table (`MethodActions`) of the `ProxyInstance`. A non-null `coverage` handler replaces the original logic; a `null` `coverage` makes the proxy fall back to reflection over the real target.

3) **Call the member through the proxy** — `int result = proxy.Add(2, 3);`

   **Expected result:** the call funnels into `ProxyInstance.Invoke`, which dispatches on the method name and runs the hooks.

4) **Observe the hook order** — for a member with all three hooks, the order is: `start` → `coverage` (or reflection fallback when `coverage == null`) → `end`. `start` and `coverage` can chain the return value through the `previous` argument of `ProxyHandler`; the `coverage` (or reflection) result is returned to the caller.

   **Expected result:** with the hooks from step 2, the console prints `[start] ...`, then `[coverage] ...`, then `[end] ...`, then `result = 5`.

5) **Reverse-map** — `var original = Aop.GetTarget<Counter>(proxy);`

   **Expected result:** `original` is the original `Counter` instance the proxy was created for (the mapping is registered by the generated `Aop()` extension via `Aop.Map`).

#### 5. Verification

Run one of the shipped demos — `Examples/AOP/WPF/Demo` (WPF) or `Examples/AOP/Avalonia/Demo` (Avalonia) — or the console program in step 6, and confirm the hook order:

- reading `Name` shows the getter **start** hook;
- writing `Name` shows the setter **end** hook;
- calling `Reset()` shows the **coverage** hook that cancels the default logic;
- adding / removing a member shows the `AOP_OnMemberAdded` / `AOP_OnMemberRemoved` **end** hooks.

In the WPF demo these are driven by the buttons `Click0`..`Click4` and surface as `MessageBox` popups; the Avalonia demo uses toast `Notification`s.

#### 6. Complete Code

A single, self-contained console program. Create a `net9.0` console project, add `VeloxDev.Core`, and replace `Program.cs`:

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

        // One SetProxy call registers the whole (start, coverage, end) triple.
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

        // Reflection-fallback path: coverage is null, only an end hook is attached.
        proxy.SetProxy(ProxyMembers.Setter, nameof(Counter.Total),
            null,
            null,
            (parameters, previous) =>
            {
                Console.WriteLine($"[end] Total set to {parameters?[0]} (reflection ran the real setter)");
                return null;
            });

        // Getter start hook.
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

The symbols are self-consistent: `Counter`, `Total`, `Add`, `proxy`, `result`, `total`, and `original` are all defined above; the generated `Counter_AopDemo_Aop` interface and `Aop()` extension are produced by the source generator from the `[AspectOriented]` members.

**Expected console output (derived statically, not recorded from a run):**

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

#### 7. Run Declaration

- ⚠️ Not actually run — statically verified only. The shipped demos under `Examples/AOP/WPF/Demo` and `Examples/AOP/Avalonia/Demo` were read as evidence, but no console/WPF/Avalonia project exercising the AOP proxy was compiled and executed in this session, so the console output above is a static derivation rather than a recorded transcript.
