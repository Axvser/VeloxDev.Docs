# `TickManager` — Events

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 1037-1042 (the static events) and 1024-1027 (the subscription that forwards a channel's own events to them).

```csharp
public static event EventHandler<TickChannelEventArgs>? OnChannelStarted;
public static event EventHandler<TickChannelEventArgs>? OnChannelPaused;
public static event EventHandler<TickChannelEventArgs>? OnChannelResumed;
public static event EventHandler<TickChannelEventArgs>? OnChannelStopped;
```

| Event | Raised when | Payload |
|---|---|---|
| `OnChannelStarted` | A channel transitions from stopped to running, at the end of `Start` | `TickChannelEventArgs` with the channel name |
| `OnChannelPaused` | `Pause()` actually paused the channel | same |
| `OnChannelResumed` | `Resume()` actually unpaused the channel | same |
| `OnChannelStopped` | A channel that **was** running has been stopped, at the end of `StopAsync` | same |

#### `TickManager.OnChannelStarted`

**Signature:**
`public static event EventHandler<TickChannelEventArgs>? OnChannelStarted`

**Notes:**
- Raised by `LoopChannel.Started`, which `Start()` fires at its very end (line 326) — after the pumps have been created and started, so a handler can query `IsRunning` and get `true`.
- **Not** raised by a redundant `Start` on a running channel: `Start` returns at line 276 before it reaches the event.

#### `TickManager.OnChannelPaused`

**Signature:**
`public static event EventHandler<TickChannelEventArgs>? OnChannelPaused`

**Notes:**
- Raised by `LoopChannel.Paused` from `Pause()` only after the guard, so an already-paused channel does not re-raise it.
- `TogglePause()` raises this or `OnChannelResumed`, never both.

#### `TickManager.OnChannelResumed`

**Signature:**
`public static event EventHandler<TickChannelEventArgs>? OnChannelResumed`

**Notes:**
- Raised by `LoopChannel.Resumed` from `Resume()` after its guard.
- After a rate of `0`, `Resume()` raises this even though the clock still does not advance — the pause really was lifted; the freeze is a separate state.

#### `TickManager.OnChannelStopped`

**Signature:**
`public static event EventHandler<TickChannelEventArgs>? OnChannelStopped`

**Notes:**
- Raised by `LoopChannel.Stopped` from `StopAsync` (line 373), after the pumps are joined and the statistics reset.
- **Not** raised when `StopAsync` is called on a channel that is not running: `StopAsync` returns at line 331 before reaching the event.
- `RestartAsync` raises it once per restart, followed by `OnChannelStarted` from the `Start()` at its end.

## How the forwarding works

`LoopChannel` declares its own instance events (`Started`, `Paused`, `Resumed`, `Stopped`, lines 169-172). `GetOrCreateChannel` subscribes them exactly once, at channel construction, and re-raises each with a fresh `TickChannelEventArgs` carrying the channel name (lines 1021-1029):

```csharp
private static LoopChannel GetOrCreateChannel(string name)
{
    return _channels.GetOrAdd(name, n =>
    {
        var ch = new LoopChannel(n);
        ch.Started += (s, e) => OnChannelStarted?.Invoke(s, new TickChannelEventArgs(n));
        ch.Paused += (s, e) => OnChannelPaused?.Invoke(s, new TickChannelEventArgs(n));
        ch.Resumed += (s, e) => OnChannelResumed?.Invoke(s, new TickChannelEventArgs(n));
        ch.Stopped += (s, e) => OnChannelStopped?.Invoke(s, new TickChannelEventArgs(n));
        return ch;
    });
}
```

Three consequences follow from that shape, and all three matter to a subscriber:

- **The events are process-wide.** `_channels` is a `static` dictionary and the events are `static`, so a subscription receives events from *every* channel. Filter on `e.ChannelName` if you care about one.
- **The sender is the `LoopChannel`, not `TickManager`.** The lambda passes `s` through unchanged, so `s is TickManager` is never true. The channel name is in the payload instead.
- **Subscription is one-shot per channel.** Wiring happens inside the `GetOrAdd` factory, so a channel gets exactly one forwarding chain no matter how many times `GetOrCreateChannel` is called.

**Example (subscribing):**
```text
// Format used by this wiki's Quick Start program
TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"[event]   OnChannelStarted -> {e.ChannelName}");
TickManager.OnChannelPaused  += (_, e) => Console.WriteLine($"[event]   OnChannelPaused  -> {e.ChannelName}");
TickManager.OnChannelResumed += (_, e) => Console.WriteLine($"[event]   OnChannelResumed -> {e.ChannelName}");
TickManager.OnChannelStopped += (_, e) => Console.WriteLine($"[event]   OnChannelStopped -> {e.ChannelName}");
```

**Notes:**
- Handlers run on whatever thread caused the transition — the caller's thread for `Start`, `Pause`, `Resume` and `TogglePause`; the awaiter's continuation context for the end of `StopAsync` and `RestartAsync`. A handler that touches UI must marshal.
- An exception thrown from a handler propagates to the caller of `Start` / `Pause` / `Resume`, because the invocation is not guarded. It does **not** affect the loop, which is already running (or already stopped) by then.
- There is no unsubscribe-on-dispose machinery and no weak-reference subscription: a handler keeps its target alive for the life of the process, since these are static events.
