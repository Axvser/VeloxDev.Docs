# Weak Types — API Reference

Namespace `VeloxDev.WeakTypes` (package `VeloxDev.Core`) ships four sealed, generic, thread-safe containers that hold their payloads by **weak reference**, so a long-lived owner — an event publisher, a job backlog, a history stack, a cache — never roots the objects it refers to.

All four types are evidence-backed: source lives in `Src/Core/VeloxDev.Core/WeakTypes/`, and behaviour is pinned by the MSTest suite in `Src/Core/VeloxDev.Core.Test/WeakTypes/`.

| Container | Weakness model | Page |
|---|---|---|
| `WeakDelegate<TDelegate>` | Handlers stored as `WeakReference<Delegate>`; a cached combined delegate keeps the invoke path lock-free | [WeakDelegate](00_WeakDelegate/index.md) |
| `WeakQueue<T>` | Items held by `Queue<WeakReference<T>>` — FIFO | [WeakQueue](01_WeakQueue/index.md) |
| `WeakStack<T>` | Items held by `Stack<WeakReference<T>>` — LIFO | [WeakStack](02_WeakStack/index.md) |
| `WeakCache<TTargetKey,TCacheKey>` | Value bound to a weak key via `ConditionalWeakTable` — the entry dies with its key | [WeakCache](03_WeakCache/index.md) |

## Namespace and constraints

- All four types are declared in the single namespace `VeloxDev.WeakTypes` and ship in the `VeloxDev.Core` package.
- Type parameters are constrained at the class level: `WeakQueue<T>` and `WeakStack<T>` require `where T : class`; `WeakDelegate<TDelegate>` requires `where TDelegate : Delegate`; both `WeakCache<TTargetKey,TCacheKey>` parameters require `class`.
- Every type is internally locked: mutations, counting and enumeration take an internal `lock`.

## Choosing a container

- Publish-to-many with a subscriber lifecycle that must not be kept alive → `WeakDelegate` (weak multicast handler set).
- Producer/consumer backlog that must not keep queued jobs alive → `WeakQueue`.
- Last-in-first-out history that must not keep recent frames alive → `WeakStack`.
- Attach cached data to a transient target without rooting the target → `WeakCache`.
