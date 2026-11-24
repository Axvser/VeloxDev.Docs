# Tick loop

Each channel runs two loops on dedicated threads (or two tasks on WASM): an update loop that dispatches every active behaviour once per frame, and a fixed loop that catches up on missed steps. The per-frame cost is linear in registered behaviours. The fixed loop is the interesting one, because catch-up is bounded twice — per call and in accumulated debt.

Notation: $b$ active behaviours in a channel, $c$ fixed steps advanced in one call, $s$ lifecycle/error subscribers, $a$ queued main-thread actions.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| Update frame | $O(b) + O(64 + a)$ | $O(b)$ cached array | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:511` |
| Fixed update, one call | $O(c b)$, $c \le 8$ | $O(1)$ per step | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:478` |
| Register / unregister | $O(1)$ enqueue + $O(1)$ apply | $O(1)$ | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:432` |
| Wrapper cache rebuild | $O(b \log b)$ avg, $O(b^2)$ worst, at most once per second | fresh $O(b)$ array | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:874` |
| Channel lookup | $O(1)$ avg | — | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:1021` |
| Timeline sample | $O(1)$ | — | `Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs:433` |
| Error report | $O(s)$ + exception | — | `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:1052` |

## One pass per frame over a cached array

The update pass iterates a cached wrapper array and stops the current pass if a behaviour sets `Handled`:

```csharp
var wrappers = GetCachedWrappers();
for (int i = 0; i < wrappers.Length; i++)
{
    if (frameArgs.Handled || token.IsCancellationRequested) break;
    var w = wrappers[i];
    if (w is { IsActive: true, Behavior: not null })
    {
        try { w.Behavior.InvokeUpdate(frameArgs); }
        catch (Exception ex) { ReportBehaviorError(Name, "Update", ex); }
    }
}
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:693-703`

There are two passes, Update and LateUpdate, so the frame is $2b$ dispatch calls in the worst case. The wrapper array is rebuilt only when registrations changed or the cache is older than one second, and the rebuild insertion-sorts by execution order. That makes steady-state frames $O(b)$ with an amortized $O(b \log b)$ rebuild.

## Fixed update catches up, but only so far

The sampler returns how many fixed steps are owed, and the loop runs each one with its own frame arguments:

```csharp
var count = _fixedSampler.Advance(out var sample);
if (count > 0)
{
    ...
    for (var i = 0; i < count; i++)
    {
        var fixedFrameArgs = CreateFrameEventArgs(...);
        ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);
        _frameEventArgsPool.Return(fixedFrameArgs);
    }
}
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs:478-496`

Two caps bound $c$. `MaxStepsPerCall` (8) limits steps per call; `MaxPendingSteps` (64) limits retained debt, with the excess forgiven and counted as dropped. A long hitch therefore costs at most $8b$ dispatches in the next call:

$$
T_{\text{fixed}} = O(c\,b),\qquad c \le 8
$$

```plot
{
  "title": "Fixed-update dispatch per call",
  "grid": true,
  "xAxis": { "domain": [0, 100] },
  "yAxis": { "domain": [0, 800] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "one step per frame, b behaviours" },
    { "fn": "8*x", "color": "#f472b6", "title": "catch-up cap, c = 8" }
  ]
}
```

The step total is derived from the delivered integer count, not from a wall-clock remainder, so the fixed loop does not drift after a catch-up burst.

## What does not cost per frame

Subscribers are not on the frame path. Channel lifecycle events and error reports invoke their handlers once per transition or error, $O(s)$; behaviours are dispatched from the array, not through an event. The bus is a shared timeline sampled in $O(1)$; pause and rate propagate through a stall gate, and a stalled loop pays no dispatch at all. Registration is an enqueue; it is applied on the next frame in $O(1)$.

## Memory and semantics

The channel stores one wrapper per active behaviour and one cached array, rebuilt by allocation. Each queue holds pending registrations or actions, and three object pools are capped at 50 entries. Two dedicated threads per channel are the real fixed cost when the OS thread path is used; the async path avoids them. Note that `Handled` is reset every frame and only breaks the current pass — setting it in Update skips the LateUpdate pass but does not stop the channel.
