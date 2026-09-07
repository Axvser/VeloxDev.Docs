# Weak Types — Prerequisites

## 1. Supported targets

The supported target frameworks come from the `<TargetFrameworks>` element of `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`:

```xml
<TargetFrameworks>netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0</TargetFrameworks>
```

So the four weak types are consumable from .NET Framework 4.6.1+, .NET Core 3.0+, .NET 5+ and any platform that can reference a `netstandard2.0` library. There is no target-specific code inside them — they are plain collections over `WeakReference<T>` and `ConditionalWeakTable<TKey, TValue>`.

**Expected result:** the Quick Start console program on the final page targets `net10.0` (the same target as the test project `VeloxDev.Core.Test`). That is a *tested* configuration, not the minimum — the library itself supports the older targets listed above.

## 2. SDK / runtime

The weak types need no source generator and no runtime service, so *consuming* them only requires the SDK implied by your chosen target framework. Everything recorded in this Quick Start was built and run with the .NET SDK 9.0 / 10.0 toolchains.

**Expected result:** `dotnet --list-sdks` shows the SDK you will build with (an SDK 9.0+ toolchain is enough).

## 3. Package manager

NuGet / the `dotnet` CLI. All examples on the following pages use `dotnet` commands and a `.csproj`.

**Expected result:** `dotnet` resolves to an SDK 9.0+ toolchain.

## 4. Required services

None. The types are plain .NET collections inside `VeloxDev.Core`; they need no database, no network, no message bus and — unlike other VeloxDev features — no platform adapter. A plain console host is enough to observe collection and GC behaviour.

**Expected result:** you can follow the rest of this Quick Start with an empty folder and a text editor.

## 5. Where the behavioural evidence lives

There is **no dedicated GUI demo** for the weak types (the `Examples/` tree has demos only for Workflow, MVVM, Theme, Transition, AOP and MonoBehaviour). The authoritative behavioural evidence is the MSTest suite under `Src/Core/VeloxDev.Core.Test/WeakTypes/`:

- `WeakDelegateTests.cs` — subscribe/invoke, remove, clone, the combined-delegate cache and null-handler tolerance.
- `WeakQueueTests.cs` — FIFO order, peek-without-remove, `Clear`, `EnqueueRange`, null guards, enumeration and `TrimExcess`.
- `WeakStackTests.cs` — LIFO order, peek-without-remove, `Clear`, `PushRange`, null guards, enumeration and `TrimExcess`.
- `WeakCacheTests.cs` — add/update/get, overwrite, remove, `ForeachCache`, and cleanup-triggered eviction bookkeeping.

The runnable program on the last sub-page reproduces the *collect-after-GC* behaviour that unit tests deliberately do not assert (see the [GC Behavior](../07_gc-behavior/) page for why).

**Expected result:** after reading this page you know the feature is headless, needs no external setup, and is verified by tests rather than by a demo.
