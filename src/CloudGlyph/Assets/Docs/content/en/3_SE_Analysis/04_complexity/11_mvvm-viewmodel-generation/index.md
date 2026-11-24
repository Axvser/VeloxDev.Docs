# MVVM viewmodel generation

The generator itself has no runtime cost: it emits ordinary C# partial members at compile time, incrementally, so only changed types regenerate. What matters at runtime is the shape of the emitted code — property setters that are constant-time plus subscriber fan-out, command pipelines with a queue, and collection hooks that copy items into arrays per event.

Notation: $s$ event subscribers, $k$ collection items in one change, $p$ pending commands, $a$ active commands, $M$ members per type.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| Generation | $O(\text{types} \times M)$, compile-time, incremental | compile-time only | `Src/Generators/VeloxDev.Core.Generator/MVVM.cs:16` |
| Generated property set | $O(1) + O(s)$ | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:546` |
| Generated property get (collection) | $O(1)$ tracker lookup | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:701` |
| Collection-change dispatch | $O(k)$ per event | $O(k)$ arrays | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:852` |
| Collection replacement | $O(k)$ | $O(k)$ | `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:741` |
| Register a collection handler | $O(1)$ avg | $O(1)$ per pair | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs:24` |
| Command first access | $O(1)$ lazy construction | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs:653` |
| Command accept / enqueue | $O(1) + O(s)$ | $O(1)$ per execution | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:573` |
| Command finish + drain | $O(k s)$ worst | $O(p)$ pending | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:702` |
| `Interrupt` / `Clear` | $O(a s)$ / $O((a+p)s)$ | $O(a+p)$ | `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:762` |

## A property set is constant plus fan-out

The default setter compares, stores the old value, invokes the two change hooks, assigns, then raises `PropertyChanged`:

```csharp
if (global::System.Object.Equals(field, value)) return;
var old = field;
OnPropertyChanging(nameof(P));
OnXxxChanging(old, value);
field = value;
OnXxxChanged(old, value);
OnPropertyChanged(nameof(P));
```

Source: `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:554-564`

The `partial void` hooks are erased when unimplemented, and `PropertyChanged?.Invoke` does not allocate when there are no subscribers. So the steady-state cost is:

$$
T_{\text{set}} = O(1) + O(s) + T_{\text{Equals}}
$$

Whether `T_{\text{Equals}}` boxes is type-dependent: the generated call uses `Object.Equals(object, object)`, so value-type properties box both operands. That is an *inferred* constant-factor cost, not an asymptotic one.

## Collection events copy before they dispatch

The generated collection handler builds arrays of old and new items, calls the base virtual hook, then switches on the action:

```csharp
switch (e.Action)
{
    case NotifyCollectionChangedAction.Add:
        ...
        OnItemAddedToItems(e.NewItems.Cast<T>().ToArray());
        break;
```

Source: `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs:857-881`

Each hook call re-enumerates the items into another array, so one `Add` is about $2k$ work and a `Replace` (old plus new) about $4k$. The subscription itself is a weak table keyed by the collection, with a `(method, target)` comparer so the same handler is not installed twice.

## Command execution is a queue, not a lock-free call

An accepted execution takes the state lock once, adds to the active set or the pending queue, and releases before starting the body:

```csharp
await _stateLock.WaitAsync();
...
if (_active.Count < maxConcurrency) { _active.Add(item); accepted = true; }
else { _pendingQueue.Enqueue(item); }
...
_stateLock.Release();
...
_ = ExecuteCoreAsync(item);
```

Source: `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:589-631`

Completion removes from the active set in $O(1)$ and drains pending items while capacity allows:

```csharp
while (pending > 0 && active < maxConcurrency && !_isForceLocked)
{
    ...
}
```

Source: `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs:926-933`

Each drained item raises events, so a completion that starts $k$ queued commands costs $O(k s)$ when $s$ subscribers are attached. With no subscribers the event raiser returns before allocating a copy.

```plot
{
  "title": "Command completion drain",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(k) state transitions" },
    { "fn": "4*x", "color": "#f472b6", "title": "O(k*s) with 4 subscribers" }
  ]
}
```

## Memory

A generated command is a lazily created field plus a semaphore, a queue, a hash set and sixteen delegate slots — constant per command instance. Live executions cost $O(p)$ pending items and $O(a)$ active items, each one event-args object and an optional cancellation source. Type-parameterized commands hold one command per type in a `ConcurrentDictionary`, so their per-instance cost is $O(T)$ for $T$ used parameter types.
