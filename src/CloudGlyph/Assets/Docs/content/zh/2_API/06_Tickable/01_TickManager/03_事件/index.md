# `TickManager` — 事件

源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 1037-1042 行（静态事件）与第 1024-1027 行（把通道自身事件转发到它们的订阅）。

```csharp
public static event EventHandler<TickChannelEventArgs>? OnChannelStarted;
public static event EventHandler<TickChannelEventArgs>? OnChannelPaused;
public static event EventHandler<TickChannelEventArgs>? OnChannelResumed;
public static event EventHandler<TickChannelEventArgs>? OnChannelStopped;
```

| 事件 | 触发时机 | 载荷 |
|---|---|---|
| `OnChannelStarted` | 通道从停止转为运行，位于 `Start` 末尾 | `TickChannelEventArgs`，带通道名 |
| `OnChannelPaused` | `Pause()` 确实暂停了通道 | 同上 |
| `OnChannelResumed` | `Resume()` 确实解除了暂停 | 同上 |
| `OnChannelStopped` | 一个**本来在运行**的通道已被停止，位于 `StopAsync` 末尾 | 同上 |

#### `TickManager.OnChannelStarted`

**签名：**
`public static event EventHandler<TickChannelEventArgs>? OnChannelStarted`

**说明：**
- 由 `LoopChannel.Started` 触发，`Start()` 在它自己的最后一句触发（第 326 行）—— 此时两个泵已经创建并启动，所以处理器里查询 `IsRunning` 会得到 `true`。
- 对已在运行的通道重复调用 `Start` **不会**触发它：`Start` 在第 276 行就返回了。

#### `TickManager.OnChannelPaused`

**签名：**
`public static event EventHandler<TickChannelEventArgs>? OnChannelPaused`

**说明：**
- 由 `Pause()` 中的 `LoopChannel.Paused` 触发，只在其保护之后，所以已暂停的通道不会重复触发。
- `TogglePause()` 触发它或 `OnChannelResumed`，不会两者都触发。

#### `TickManager.OnChannelResumed`

**签名：**
`public static event EventHandler<TickChannelEventArgs>? OnChannelResumed`

**说明：**
- 由 `Resume()` 中的 `LoopChannel.Resumed` 触发，在其保护之后。
- 速率为 `0` 之后，`Resume()` 也会触发它，尽管时钟仍不前进 —— 暂停确实被解除了；冻结是另一个状态。

#### `TickManager.OnChannelStopped`

**签名：**
`public static event EventHandler<TickChannelEventArgs>? OnChannelStopped`

**说明：**
- 由 `StopAsync` 中的 `LoopChannel.Stopped` 触发（第 373 行），在泵已 join、统计已重置之后。
- 对未运行的通道调用 `StopAsync` 时**不会**触发：`StopAsync` 在第 331 行就返回了。
- `RestartAsync` 每次重启触发它一次，随后由末尾的 `Start()` 触发 `OnChannelStarted`。

## 转发是怎么接的

`LoopChannel` 声明了自己的实例事件（`Started`、`Paused`、`Resumed`、`Stopped`，第 169-172 行）。`GetOrCreateChannel` 在通道构造时把它们订阅一次，并用新建的 `TickChannelEventArgs`（带通道名）各自重新触发（第 1021-1029 行）：

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

从这个写法可以推出三条对订阅者都重要的结论：

- **事件是进程范围的。** `_channels` 是静态字典，事件也是 `static`，所以一个订阅会收到*所有*通道的事件。只关心某一个通道时请按 `e.ChannelName` 过滤。
- **sender 是 `LoopChannel`，不是 `TickManager`。** 那个 lambda 原样透传 `s`，所以 `s is TickManager` 永远为假。通道名在载荷里。
- **每个通道只订阅一次。** 接线发生在 `GetOrAdd` 工厂内部，所以无论 `GetOrCreateChannel` 被调用多少次，一个通道只有一条转发链。

**示例（订阅）：**
```text
// 本 Wiki 快速开始程序使用的格式
TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"[event]   OnChannelStarted -> {e.ChannelName}");
TickManager.OnChannelPaused  += (_, e) => Console.WriteLine($"[event]   OnChannelPaused  -> {e.ChannelName}");
TickManager.OnChannelResumed += (_, e) => Console.WriteLine($"[event]   OnChannelResumed -> {e.ChannelName}");
TickManager.OnChannelStopped += (_, e) => Console.WriteLine($"[event]   OnChannelStopped -> {e.ChannelName}");
```

**说明：**
- 处理器运行在造成该迁移的那个线程上 —— `Start`、`Pause`、`Resume`、`TogglePause` 是调用方线程；`StopAsync` / `RestartAsync` 末尾是 awaiter 的续体上下文。触碰 UI 的处理器必须自行封送。
- 处理器抛出的异常会传播给 `Start` / `Pause` / `Resume` 的调用方，因为调用没有保护。它**不影响**循环 —— 到那时循环已经在跑（或已经停下）。
- 没有基于 dispose 的退订机制，也没有弱引用订阅：由于是静态事件，处理器会让它的目标对象活到进程结束。
