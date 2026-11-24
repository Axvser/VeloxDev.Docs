# Aspect-Oriented Programming

Attach before / replace / after hooks to a property getter, a property setter and a method without editing their bodies. The generator emits a mirror interface and a proxy; calling through `Aop()` is what makes the hooks run.

## 1. Prerequisites

- **Target framework**: `VeloxDev.Core` builds the AOP runtime only when the `NET` symbol is defined, so the consumer must target **.NET 5.0 or later** (`netstandard2.0` and `netframework4.6.1` do not carry `VeloxDev.AspectOriented`). The sample uses `net8.0`.
- **`VeloxDev.Core`** and **`VeloxDev.Core.Generator`** (the analyzer; a NuGet reference to Core carries it, a `ProjectReference` does not).
- .NET SDK 8.0 or later. No services are required. A GUI is not needed.

## 2. Install / Add Dependency

```text
dotnet new console -n AopQuickStart
cd AopQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** both packages restore; the project targets `net8.0`; the generator emits `*_AOP.g.cs`, `*_AopExt.g.cs`, `<Interface>.g.cs` and `<Interface>Proxy.g.cs` after the first build.

## 3. Basic Setup / Registration

Mark the class `partial` and put `[AspectOriented]` on each member to be intercepted. A field also needs a property generator attribute (`[VeloxProperty]`); a normal property works on its own.

```csharp
using VeloxDev.AspectOriented;

public partial class CounterViewModel
{
    [AspectOriented]
    public int Value { get; set; }

    [AspectOriented]
    public void Reset() => Value = 0;
}
```

**Expected result:** `counter.Aop()` resolves through `using VeloxDev.AspectOriented;` and returns the generated interface. The class itself does not implement that interface; the proxy does.

## 4. Core Usage (Step by Step)

### 4.1 Get the proxy

`Aop()` caches one proxy per target and returns it. The returned interface mirrors every `[AspectOriented]` member, so the caller uses it like the original object. `AopCache.Resolve<TClass, TInterface>` is the same cache underneath; `Aop.GetTarget<TTarget>(proxy)` is the reverse lookup.

```csharp
var counter = new CounterViewModel();
var proxy = counter.Aop();
```

**Expected result:** two calls return the same proxy for the same object. Calls on `counter` directly still bypass every hook.

### 4.2 Install the three stages

`SetProxy` takes the member kind, the member's plain name, and three delegates in the order start / coverage / end. A stage is `ProxyHandler(object?[]? parameters, object? previous)`.

- `start` runs before the member; its return value becomes the next stage's `previous`.
- `coverage` replaces the member when non-null: the body does not run and its return value becomes the member's result.
- `end` runs after the member; its return value is discarded.

For a getter `parameters` is `null`; for a setter its single element is the value being written; for a method they are the method's own arguments.

```csharp
proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) => { Console.WriteLine($"[setter after] {parameters?[0]}"); return null; });
```

**Expected result:** assigning `proxy.Value = 7` first runs the real setter, then prints `[setter after] 7`.

### 4.3 Read, write and call through the proxy

```csharp
Console.WriteLine(proxy.Value);
proxy.Value = 7;
proxy.Reset();
```

**Expected result:** the getter hook, then the real getter; the setter hook after the write; `Reset` is intercepted like any method.

### 4.4 Replacing a member

Installing `coverage` on `Reset` prevents its body from running. The handler's return value is the method's result (for a `void` method it is ignored).

```csharp
proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);
```

**Expected result:** `proxy.Reset()` prints `[reset replaced]` and leaves `Value` at 7.

### 4.5 Composition and replacement semantics

Installing on the same member twice **replaces** all three stages; there is no way to keep one stage and swap another. To remove a member's hooks, install a set whose three stages are all `null`. A `[VeloxProperty][AspectOriented]` field is supported: the generated property becomes the intercepted member, and its name is derived exactly as the MVVM generator derives it (`_name` becomes `Name`). An overloaded method cannot be hooked — the interception key is the bare method name.

`SetProxy` refuses an object that is not a proxy instead of silently installing hooks that never run.

**Expected result:** a second `SetProxy` call on `Value`/`Getter` replaces the first handler; installing on `counter` (not `proxy`) throws `InvalidOperationException`.

## 5. Verification

Run the complete program. The order proves the stages:

```text
[getter before]
read: 0
[setter after] 7
[reset replaced]
[getter before]
read after replaced Reset: 7
```

The last read is 7, not 0: the replaced `Reset` never executed its body.

## 6. Complete Code

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();

proxy.SetProxy(ProxyMembers.Getter, nameof(CounterViewModel.Value),
    (parameters, previous) => { Console.WriteLine("[getter before]"); return null; },
    null,
    null);

proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) => { Console.WriteLine($"[setter after] {parameters?[0]}"); return null; });

proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);

Console.WriteLine($"read: {proxy.Value}");
proxy.Value = 7;
proxy.Reset();
Console.WriteLine($"read after replaced Reset: {proxy.Value}");

public partial class CounterViewModel
{
    [AspectOriented]
    public int Value { get; set; }

    [AspectOriented]
    public void Reset() => Value = 0;
}
```

Demo evidence: `Examples/AOP/WPF/Demo/MainWindow.xaml.cs` installs the same three stages; `Examples/AOP/WPF/Demo/TeamViewModel.cs` shows `[VeloxProperty][AspectOriented]` on a field.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`, `AspectHooks.cs`, `Aop.cs`, `AspectOrientedAttribute.cs`, `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`, `Writers/AopWriter.cs` and the WPF/Avalonia AOP demos. No build was performed in this environment.
