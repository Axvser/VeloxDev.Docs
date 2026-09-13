# Weak Types — Quick Start

The **weak-types** feature ships four framework-agnostic collection types that hold their contents through *weak references*, so an entry never keeps its target alive. They exist to prevent the classic .NET memory leak where a long-lived publisher, event source or cache keeps short-lived subscribers and keys reachable through a strong reference long after they are done.

All four types live in the `VeloxDev.WeakTypes` namespace inside the `VeloxDev.Core` package (source folder `Src/Core/VeloxDev.Core/WeakTypes/`), have no UI adapter and no runtime dependency, and are `sealed`:

- `WeakDelegate<TDelegate>` (`where TDelegate : Delegate`) — an event-like, multi-handler sink that stores each handler as a `WeakReference<Delegate>`. Subscribers are dropped automatically once they are collected, so a publisher never outlives its value to a dead listener. Reads go through a lock-free cached combined delegate.
- `WeakQueue<T>` (`where T : class`) — a FIFO buffer of `WeakReference<T>` entries; dead entries are pruned on access.
- `WeakStack<T>` (`where T : class`) — the LIFO counterpart of `WeakQueue<T>`.
- `WeakCache<TTargetKey, TCacheKey>` (`where TTargetKey : class`, `where TCacheKey : class`) — a per-target key/value map built on `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>`. The value dies with its target key instead of keeping the key alive.

Each type is thread-safe through an internal lock, mirrors the shape of its strong `System.Collections.Generic` counterpart, and is exercised by the MSTest suite in `Src/Core/VeloxDev.Core.Test/WeakTypes/` (`WeakDelegateTests.cs`, `WeakQueueTests.cs`, `WeakStackTests.cs`, `WeakCacheTests.cs`). There is **no dedicated GUI demo** for this feature — the tests are the primary behavioural evidence, and the runnable program on the last sub-page exercises all four types headless.

The package `VeloxDev.Core` multi-targets `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`; nothing else needs to be installed.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages (they build toward the single runnable program on the last page):

- [00 Prerequisites](00_prerequisites/) — supported targets, SDK/runtime, and where the behavioural evidence lives
- [01 Install](01_install/) — add `VeloxDev.Core` from NuGet or project-reference it from this repo
- [02 Pick a Collection](02_choose-a-collection/) — which of the four types fits a scenario (leaks, FIFO/LIFO buffers, per-target values)
- [03 WeakDelegate](03_weak-delegate/) — event-like weak subscription: `AddHandler` / `RemoveHandler` / `GetInvocationList` / `Invoke` / `Clone`
- [04 WeakQueue](04_weak-queue/) — FIFO processing of ephemeral work items
- [05 WeakStack](05_weak-stack/) — LIFO undo/redo-style stacks that cannot hold items alive
- [06 WeakCache](06_weak-cache/) — target-keyed values that die with their key
- [07 GC Behavior](07_gc-behavior/) — what “weak” really means, sweep-on-access, and the Debug/Release caveats
- [08 Verify & Complete Code](08_verify-and-complete-code/) — the tests, the single runnable program, the recorded output, and the run declaration
