# Weak Types — WeakDelegate<TDelegate>

`WeakDelegate<TDelegate>` (source `Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs`) is an event-like, multi-handler sink whose handler list holds `WeakReference<Delegate>` entries instead of strong delegate references. Use it when a publisher outlives many short-lived subscribers and you want the *list* to stop keeping dead subscribers alive — the counterpart of a strong C# event, where the publisher's delegate chain pins every subscriber.

The generic argument must derive from `System.Delegate` (for example `WeakDelegate<Action<string>>`).

## 1. Subscribe and invoke

`AddHandler` appends a handler as a weak reference; `Invoke(object?[] objects)` fires the current combined delegate through `DynamicInvoke`:

```csharp
using System;
using VeloxDev.WeakTypes;

var counter = new Counter();                // helper classes from the Complete Code page
var subscriber = new Subscriber(counter);
var changed = new WeakDelegate<Action<string>>();

changed.AddHandler(subscriber.Handle);      // stored as WeakReference<Delegate>
changed.Invoke(["hello"]);                  // object?[] argument -> DynamicInvoke
Console.WriteLine($"counter: {counter.Value}");   // 1
```

**Expected result:** the handler ran once (`counter.Value == 1`), mirroring the unit test `AddHandler_And_Invoke_CallsHandler` in `WeakDelegateTests.cs` (there with an `Action<int>` and `Invoke([42])`). `AddHandler(null)` is a no-op, matching `AddHandler_Null_NoException`.

## 2. Remove a handler

`RemoveHandler` scans the list backwards and removes every entry whose target equals the handler, then rebuilds the cache:

```csharp
changed.AddHandler(subscriber.Handle);
changed.RemoveHandler(subscriber.Handle);   // matching entries removed from the weak list
changed.Invoke(["nobody"]);
Console.WriteLine($"counter: {counter.Value}");   // still 1
```

**Expected result:** after removal the invoke does not call the handler, matching `RemoveHandler_RemovesFromHandlerList`.

## 3. The cached combined delegate (read this before relying on GC)

To avoid locking and reflection on the hot path, the type keeps a *cached combined delegate* (`_combinedDelegate`, a `volatile` field). `GetInvocationList()` returns it directly once built (lock-free), and rebuilds it only when the cache is empty:

```csharp
var typed = changed.GetInvocationList();    // TDelegate? = Action<string>?
typed?.Invoke("hello");                     // typed, reflection-free invocation
```

Two consequences follow from the cache being a strong combined delegate:

- `AddHandler` / `RemoveHandler` take a `bool CanUpdateCache = true`. With the default, the cache is rebuilt immediately, and **every live handler merged into the cache becomes strongly reachable through it**.
- Handlers added with `CanUpdateCache: false` are written to the weak list but *not* merged into the cache. They stay collectible, so a subscriber that dies before the next rebuild is dropped by the GC.

That is why the dead-handler trick on the Complete Code page passes `CanUpdateCache: false`:

```csharp
var deadSub = new Subscriber(counter);
changed.AddHandler(deadSub.Handle, CanUpdateCache: false);   // keep out of the cache so it can be collected
```

The cache is only rebuilt on an `AddHandler` / `RemoveHandler` with `CanUpdateCache: true`, on a `GetInvocationList()` that finds no cache, or inside `Clone()`. So for a deterministic unsubscribe always call `RemoveHandler`; for a "let dead subscribers drop" design, add them with `CanUpdateCache: false` and let a later rebuild (or `Clone`) prune them.

**Expected result:** adding the same handler twice then invoking fires it twice; adding a third handler with `CanUpdateCache: false` does not change what `GetInvocationList()` returns until the next rebuild.

## 4. Snapshot with Clone

`Clone()` returns a *new* `WeakDelegate<TDelegate>` rebuilt from only the currently-live weak entries, with its cache already filled — collected subscribers are simply absent:

```csharp
var snapshot = changed.Clone();             // rebuilds from live handlers only
snapshot.Invoke(["second"]);
```

**Expected result:** a collected subscriber's handler is not invoked through the clone. This mirrors the tests `Clone_ReturnsIndependentCopy` and `MultipleHandlers_CloneInvokesAll` (the latter fires `h1` and `h2` and asserts a combined counter of `11`).
