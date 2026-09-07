# MonoBehaviour — Prerequisites

## 1. Supported targets

The supported target frameworks come from the `<TargetFrameworks>` element of `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`:

```xml
<TargetFrameworks>netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0</TargetFrameworks>
```

So the runtime is consumable from .NET Framework 4.6.1+, .NET Core 3.0+, .NET 5+ and any platform that can reference a `netstandard2.0` library.

**Expected result:** the Quick Start console program in this feature targets `net10.0`; the shipped WPF demo targets `net10.0-windows`. Those are *tested* configurations, not the minimum — the library itself supports the older targets listed above.

## 2. SDK / runtime

The `[MonoBehaviour]` feature depends on a Roslyn source generator, so you need a .NET SDK with Roslyn 4.x. SDK 9.0/10.0 were used to build and run everything recorded in this Quick Start.

For **consuming** the package you only need the SDK implied by your chosen target. For **building this repository** you additionally need the reference assemblies for `netframework4.6.1` (restored automatically as the `Microsoft.NETFramework.ReferenceAssemblies` package when the `net4x` target builds).

**Expected result:** `dotnet --list-sdks` shows the SDK you will build with.

## 3. Package manager

NuGet / the `dotnet` CLI. All examples on the following pages use `dotnet` commands and a `.csproj`.

**Expected result:** `dotnet` resolves to an SDK 9.0+ toolchain.

## 4. Required services

None. The frame loop runs entirely inside `MonoBehaviourManager` on background threads; it needs no database, no network, no message bus and no platform adapter. A plain console host is enough to observe the loop, which is why every example here is a console program.

**Expected result:** you can follow the rest of this Quick Start with an empty folder and a text editor.

## 5. Concurrency note up front

The two pumps of a channel run on separate threads (native `Thread` by default on desktop; `async` tasks on platforms without `Thread`, see the [Configure & Run the Loop](../03_configure-and-run-the-loop/) page). Hooks such as `Update` and `FixedUpdate` therefore execute concurrently with each other. The examples use `System.Threading.Interlocked` for counters so that the printed numbers are correct no matter how the two threads interleave.

**Expected result:** after reading this page you know the feature is a headless, thread-based frame loop and needs no external setup.
