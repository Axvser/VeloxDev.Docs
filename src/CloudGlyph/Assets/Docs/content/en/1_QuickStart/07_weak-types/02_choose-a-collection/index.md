# Weak Types — Pick a Collection

The four types solve different leak/lifetime problems. Use the table to choose, then jump to the matching page.

## 1. Scenario table

| Scenario | Type | Why |
|---|---|---|
| An event-like publisher that must not keep dead subscribers alive (a "weak event") | `WeakDelegate<TDelegate>` | Each handler is a `WeakReference<Delegate>`; when the subscriber is collected the handler disappears from the next rebuild. See [WeakDelegate](../03_weak-delegate/). |
| FIFO buffer of items that must not pin their producers — process work only while the producing object is still alive | `WeakQueue<T>` | Entries are `WeakReference<T>`; a queued item whose only reference is the queue is collected, and access skips/prunes dead entries. See [WeakQueue](../04_weak-queue/). |
| LIFO (undo/redo, back-stack) of short-lived states that must not keep their owner reachable | `WeakStack<T>` | Same weak-entry model as the queue, LIFO order. See [WeakStack](../05_weak-stack/). |
| A per-target value that should vanish when its target key vanishes (ephemeral side-table) | `WeakCache<TTargetKey, TCacheKey>` | Built on `ConditionalWeakTable<TTargetKey, TCacheKey>`, which does not root the key. See [WeakCache](../06_weak-cache/). |

**Expected result:** for each row you can name the exact generic type — including its type arguments — before reading the detailed page.

## 2. Shared constraints

The generic constraints come straight from the source signatures in `Src/Core/VeloxDev.Core/WeakTypes/`:

- `WeakDelegate<TDelegate>` requires `where TDelegate : Delegate` — handlers are delegate instances.
- `WeakQueue<T>` and `WeakStack<T>` require `where T : class` — items must be reference types.
- `WeakCache<TTargetKey, TCacheKey>` requires `where TTargetKey : class` **and** `where TCacheKey : class` — both the key and the value are reference types.

Value types (e.g. `int`, `struct`) are rejected at compile time because `WeakReference<T>` can only track reference-type targets. If you need a weak slot for a value, wrap it in a small class or use a nullable field guarded by your own lifetime rules.

**Expected result:** the compiler accepts `WeakQueue<SomeClass>` and rejects `WeakQueue<int>` with a constraint error.

## 3. When not to use a weak collection

- **You need the item to survive while the collection survives.** A weak collection is not a guarantee — the GC may reclaim an entry whose only reference is the weak one. If correctness requires the entry to be present (a real work queue you will drain later), keep a strong reference elsewhere.
- **You already control the lifetime.** If the subscriber/owner and the event source have a clear, bounded lifetime you manage, an explicit unsubscribe (or removing from the collection) is cheaper and more predictable than relying on GC.
- **You need `IEnumerable` ordering guarantees across GCs.** Enumeration prunes and only yields live entries, so the visible contents can change between two enumerations if a GC runs in between.
- **Keys/values are interned or static strings.** A string literal is rooted by the runtime for the whole process, so a `WeakCache<string, string>` built on literals (as in some unit tests) never actually evicts. Use real object instances when you want to observe eviction. See [GC Behavior](../07_gc-behavior/).

**Expected result:** for each "don't" case you can state which type you would *not* pick and why.
