# MonoBehaviour — `MonoBehaviourChannelEventArgs`

Namespace `VeloxDev.TimeLine`. Event payload for the manager's per-channel lifecycle events. Declared in `MonoBehaviourManager.cs`, after the manager class.

```csharp
namespace VeloxDev.TimeLine;

public sealed class MonoBehaviourChannelEventArgs(string channelName) : EventArgs
{
    public string ChannelName { get; }
}
```

### `MonoBehaviourChannelEventArgs.MonoBehaviourChannelEventArgs` (constructor)

**Signature:**

`public MonoBehaviourChannelEventArgs(string channelName)`

| Parameter | Type | Description |
|---|---|---|
| `channelName` | `string` | The channel the event refers to. |

**Returns:** `MonoBehaviourChannelEventArgs`

### `MonoBehaviourChannelEventArgs.ChannelName`

**Signature:**

`public string ChannelName { get; }`

**Returns:** `string` — the name of the channel that raised the event.

**Notes:**

- The manager raises `OnChannelStarted`, `OnChannelPaused`, `OnChannelResumed` and `OnChannelStopped` with an instance of this type; `ChannelName` is always filled.

**Source:**

`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourManager.cs` (type declared at the end of the file)
