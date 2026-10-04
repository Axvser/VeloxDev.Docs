# 门面、注册表与发布订阅

`TickManager` 同时扮演三个角色，把它们分开看，每一个都很简单。

| 角色 | 在这里的含义 | 源码 |
|---|---|---|
| 门面 | 34 个公开静态成员，全部是一句转发到某个 `LoopChannel` | `TickManager.cs` 1046-1156 |
| 注册表 | 静态 `ConcurrentDictionary<string, LoopChannel>` 加惰性工厂 | `TickManager.cs` 1017-1033 |
| 发布者 | 四个静态事件，按通道重新发布 | `TickManager.cs` 1021-1029、1037-1042 |

```mermaid
flowchart LR
    U[用户代码] -->|静态调用，通道名| F[TickManager 门面]
    F -->|GetOrCreateChannel| R["_channels ConcurrentDictionary string LoopChannel"]
    R -->|GetOrAdd 工厂，每个名字一次| L[LoopChannel 实例]
    L -->|Started / Paused / Resumed / Stopped| A[匿名转发器]
    A -->|new TickChannelEventArgs name| P["静态 OnChannel* 事件"]
    P --> S[所有订阅者，进程范围]
```

## 门面

每个公开成员都是一句转发，这正是参考文档按成员分组而不是按类型拆分的原因：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（1048-1064 行）
public static void Start(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).Start();

public static Task StopAsync(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).StopAsync();

public static void Pause(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).Pause();
```

门面除了通道字典之外不持有任何自己的状态。凡是带生命周期的东西 —— 采样器、池、队列、线程 —— 都属于某个 `LoopChannel`，而 `LoopChannel` 是 `private sealed`，所以门面是抵达它们的**唯一**途径。这正是引擎可以重写而无需改动任何一个公开签名的原因。

状态查询是门面唯一不是纯转发的地方：它们必须为不存在的通道作答，于是每个都变成带显式回退的 `TryGetValue`。

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（1107-1108 行）
public static bool IsRunning(string channel = DEFAULT_CHANNEL)
    => _channels.TryGetValue(channel, out var c) && c.IsRunning;
```

注意它与 mutator 之间刻意的不对称：`Start` **会创建**通道，`IsRunning` **不会**。`Bus` 遵循同一规则，宁可返回 `null` 也不构造 —— `TickableBusTests.BusIsNullForAChannelThatWasNeverStarted` 断言了这一点，并附言：查询不得顺手创建通道。

## 注册表

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（1017-1030 行）
private static readonly ConcurrentDictionary<string, LoopChannel> _channels = new();

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

关于这个工厂有两点是承重的：

- **转发接在工厂内部**，因此无论多少线程争抢 `GetOrCreateChannel`，每个名字只接一次。没有订阅者簿记、没有退订路径、没有重复触发。
- **通道永不移除。** `ChannelNames` 公开的是一个只会变长的列表的键。没有 `CloseChannel`；`StopAsync` 停掉泵而把 transport 留在原处，这正是 `RestartAsync` 与「重启复用同一条总线」得以成立的原因。

注册表还赋予事件它们继承来的进程级语义。由于 `_channels` 是 `static`、事件也是 `static`，一次订阅会收到所有通道的事件 —— 载荷里的通道名是唯一的区分手段，而 sender 是 `LoopChannel`（私有类型）而不是 `TickManager`。

## 发布订阅

`LoopChannel` 触发自己的实例事件；门面用新建的载荷重新触发它们。链条是：泵或 mutator → `LoopChannel` 实例事件 → 静态转发 lambda → `TickManager` 静态事件 → 所有订阅者。

| 迁移 | 触发者 | 抑制它的事件保护 |
|---|---|---|
| Started | `LoopChannel.Start`，末尾 | 开头的 `if (_isRunning) return;` —— 重复 `Start` 什么都不触发 |
| Paused | `LoopChannel.Pause` | `if (!_isRunning \|\| _bus.IsPaused) return;` |
| Resumed | `LoopChannel.Resume` | `if (!_isRunning \|\| !_bus.IsPaused) return;` |
| Stopped | `LoopChannel.StopAsync`，末尾 | 开头的 `if (!_isRunning) return;` |

这个模式**只对真实迁移诚实**：每个触发点都放在保护之后，所以一个事件意味着状态确实变了。`TogglePause` 不可能两者都触发，因为它调用 `Pause` 或 `Resume`，而这两个方法是仅有的触发点。

订阅者需要围绕两条推论来设计：

- 处理器运行在调用方线程上 —— `Start` / `Pause` / `Resume` / `TogglePause` 是调用线程，`StopAsync` / `RestartAsync` 末尾是 awaiter 的续体上下文。调用没有保护，所以抛异常的处理器会传播给调用方；到那时循环已经在跑或已经停下，因此不受影响。
- 演示**没有**订阅这些事件。它是轮询的（`MainWindow.xaml.cs` 第 31、51、164-176 行），理由写在文件里：在钩子里调 `Dispatcher.Invoke` 会被引擎的逐钩子捕获吞掉，所以演示改为发布不可变快照，让 UI 线程自己读。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 274-327（Start）、329-374（StopAsync）、384-402（Pause/Resume）、1017-1042（注册表与事件）、1105-1156（查询）行；`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs` 31、51、164-176 行；`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` 112-131 行。
