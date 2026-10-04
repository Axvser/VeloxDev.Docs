# `TickChannelEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public sealed class TickChannelEventArgs(string channelName) : EventArgs
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 1159-1162 行。

`TickManager` 四个通道事件的载荷。它与 `TickManager` 同处一个文件、是顶层类型，并且**不**派生自 `TimeLineEventArgs` —— 它派生自 `EventArgs`，因为它不携带任何可取消状态，只有一个名字。

这就是原名 `MonoBehaviourChannelEventArgs` 的那个类型；改名只改了名字。

#### 构造函数

#### `TickChannelEventArgs(string channelName)`

**签名：**
`public TickChannelEventArgs(string channelName)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channelName` | `string` | 触发该事件的通道名 |

**返回：** 新实例。参数存进 `ChannelName`。

**异常：** 无。`null` 被接受并原样存储；框架从不传它，因为通道名来自 `_channels` 字典的键。

#### 属性：`TickChannelEventArgs.ChannelName`

**签名：**
`public string ChannelName { get; }`

**返回：** `string` —— 正在上报生命周期迁移的那个通道的名字。

**示例：**
```text
// 源码：GetOrCreateChannel 中的转发（TickManager.cs 第 1024-1027 行）
ch.Started += (s, e) => OnChannelStarted?.Invoke(s, new TickChannelEventArgs(n));
ch.Paused  += (s, e) => OnChannelPaused?.Invoke(s, new TickChannelEventArgs(n));
ch.Resumed += (s, e) => OnChannelResumed?.Invoke(s, new TickChannelEventArgs(n));
ch.Stopped += (s, e) => OnChannelStopped?.Invoke(s, new TickChannelEventArgs(n));

// 只关心某一个通道的订阅者：
TickManager.OnChannelStarted += (_, e) =>
{
    if (e.ChannelName == TickManager.DEFAULT_CHANNEL) Console.WriteLine("默认通道已启动");
};
```

**说明：**
- 只读，且没有其他成员。通道名就是全部载荷 —— 事件只告诉你*哪个*通道变了，变化成什么状态要你自己调状态查询。
- 由于管理器的事件是 `static` 且进程范围的，`ChannelName` 是处理器里区分通道的唯一手段。任何只关心一个通道的订阅者都必须按它过滤。
- 交给订阅者的 `sender` 是通道的 `LoopChannel` 实例 —— 一个 `private sealed` 类型 —— 而不是 `TickManager`。把它当作不透明的，名字从本属性读。
