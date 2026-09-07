# MonoBehaviour — `MonoBehaviourChannelEventArgs`

命名空间 `VeloxDev.TimeLine`。管理器各通道生命周期事件的事件载荷。声明在 `MonoBehaviourManager.cs` 中管理器类之后。

```csharp
namespace VeloxDev.TimeLine;

public sealed class MonoBehaviourChannelEventArgs(string channelName) : EventArgs
{
    public string ChannelName { get; }
}
```

### `MonoBehaviourChannelEventArgs.MonoBehaviourChannelEventArgs`（构造函数）

**签名：**

`public MonoBehaviourChannelEventArgs(string channelName)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channelName` | `string` | 事件所指的通道。 |

**返回：** `MonoBehaviourChannelEventArgs`

### `MonoBehaviourChannelEventArgs.ChannelName`

**签名：**

`public string ChannelName { get; }`

**返回：** `string` — 触发事件的通道名称。

**说明：**

- 管理器以本类型实例触发 `OnChannelStarted`、`OnChannelPaused`、`OnChannelResumed`、`OnChannelStopped`；`ChannelName` 始终被填充。

**源码：**

`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourManager.cs`（类型声明于文件末尾）
