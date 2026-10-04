# `TickChannelEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public sealed class TickChannelEventArgs(string channelName) : EventArgs
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 1159-1162.

The payload of the four `TickManager` channel events. It is a top-level type in the same file as `TickManager` and does **not** derive from `TimeLineEventArgs` — it derives from `EventArgs`, because it carries no cancelable state, only a name.

This is the type formerly named `MonoBehaviourChannelEventArgs`; the rename changed nothing but the name.

#### Constructor

#### `TickChannelEventArgs(string channelName)`

**Signature:**
`public TickChannelEventArgs(string channelName)`

| Parameter | Type | Description |
|---|---|---|
| `channelName` | `string` | The name of the channel that raised the event. |

**Returns:** a new instance. The argument is stored in `ChannelName`.

**Exceptions:** none. `null` is accepted and stored as-is; the framework never passes it, since channel names come from the `_channels` dictionary keys.

#### Property: `TickChannelEventArgs.ChannelName`

**Signature:**
`public string ChannelName { get; }`

**Returns:** `string` — the name of the channel whose lifecycle transition is being reported.

**Example:**
```text
// Source: the forwarding in GetOrCreateChannel (TickManager.cs lines 1024-1027)
ch.Started += (s, e) => OnChannelStarted?.Invoke(s, new TickChannelEventArgs(n));
ch.Paused  += (s, e) => OnChannelPaused?.Invoke(s, new TickChannelEventArgs(n));
ch.Resumed += (s, e) => OnChannelResumed?.Invoke(s, new TickChannelEventArgs(n));
ch.Stopped += (s, e) => OnChannelStopped?.Invoke(s, new TickChannelEventArgs(n));

// A subscriber filtering to one channel:
TickManager.OnChannelStarted += (_, e) =>
{
    if (e.ChannelName == TickManager.DEFAULT_CHANNEL) Console.WriteLine("the default channel started");
};
```

**Notes:**
- Get-only, and there is no other member. The channel name is the whole payload — the event tells you *which* channel changed, and you call the status queries to find out what it changed to.
- Because the manager's events are `static` and process-wide, `ChannelName` is the only way to tell channels apart in a handler. Every subscriber that cares about one channel must filter on it.
- The `sender` handed to a subscriber is the channel's `LoopChannel` instance — a `private sealed` type — not `TickManager`. Treat it as opaque and read the name from this property instead.
