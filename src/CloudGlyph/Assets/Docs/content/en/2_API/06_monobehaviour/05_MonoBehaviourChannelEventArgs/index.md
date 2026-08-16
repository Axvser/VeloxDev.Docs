# MonoBehaviour — `MonoBehaviourChannelEventArgs`

```csharp
public sealed class MonoBehaviourChannelEventArgs(string channelName) : EventArgs
{
    public string ChannelName { get; }
}
```

#### `MonoBehaviourChannelEventArgs.MonoBehaviourChannelEventArgs` (constructor)

**Signature:**
`public MonoBehaviourChannelEventArgs(string channelName)`

| Parameter | Type | Description |
|---|---|---|
| `channelName` | `string` | The channel the event refers to. |

**Returns:** `MonoBehaviourChannelEventArgs`

#### `MonoBehaviourChannelEventArgs.ChannelName`

**Signature:**
`public string ChannelName { get; }`

**Returns:** `string`
