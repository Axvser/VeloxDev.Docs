# MonoBehaviour — `MonoBehaviourChannelEventArgs`

```csharp
public sealed class MonoBehaviourChannelEventArgs(string channelName) : EventArgs
{
    public string ChannelName { get; }
}
```

#### `MonoBehaviourChannelEventArgs.MonoBehaviourChannelEventArgs`（构造函数）

**签名：**
`public MonoBehaviourChannelEventArgs(string channelName)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channelName` | `string` | 事件所指的通道。 |

**返回：** `MonoBehaviourChannelEventArgs`

#### `MonoBehaviourChannelEventArgs.ChannelName`

**签名：**
`public string ChannelName { get; }`

**返回：** `string`
