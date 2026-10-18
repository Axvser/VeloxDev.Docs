# 门面、注册表与发布-订阅

`TickManager` 同时扮演三个角色，把它们分开才能让每个都保持简单。

| 角色 | 在此的含义 | 源码 |
|---|---|---|
| 门面 | 34 个公开静态成员，全部一行转发到 `LoopChannel` | `TickManager.cs` 1050-1156 |
| 注册表 | 静态 `ConcurrentDictionary<string, LoopChannel>` 加惰性工厂 | `TickManager.cs` 1019-1032 |
| 发布者 | 四个静态事件，按通道重新发布 | `TickManager.cs` 工厂内 1023-1031，1041-1044 |

```mermaid
flowchart LR
    U[用户代码] -->|静态调用, 通道名| F[TickManager 门面]
    F -->|GetOrCreateChannel| R["_channels ConcurrentDictionary string LoopChannel"]
    R -->|每个名字一次 GetOrAdd 工厂| L[LoopChannel 实例]
    L -->|Started / Paused / Resumed / Stopped| A[匿名转发器]
    A -->|new TickChannelEventArgs name| P["静态 OnChannel* 事件"]
    P --> S[进程范围内的所有订阅者]
```

## 门面

每个公开成员都是一行转发，这也是参考文档按成员组而不是按类型拆分的原因：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 1050-1057 行）
public static void Start(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).Start();

public static Task StopAsync(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).StopAsync();

public static void Pause(string channel = DEFAULT_CHANNEL)
    => GetOrCreateChannel(channel).Pause();
```

门面除通道字典外不拥有自己的状态。所有有生命周期的东西 —— 采样器、池、队列、线程 —— 都属于 `LoopChannel`，而 `LoopChannel` 是 `private sealed`，所以门面是到达它的*唯一*途径。这使引擎可以在不触碰任何公开签名的前提下重写。

状态查询是门面唯一不纯转发的地方：它们必须为不存在的通道作答，所以每个都变成带显式回退的 `TryGetValue`。

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 1109-1110 行）
public static bool IsRunning(string channel = DEFAULT_CHANNEL)
    => _channels.TryGetValue(channel, out var c) && c.IsRunning;
```

注意与修改器的刻意不对称：`Start` **创建**通道，`IsRunning` **不创建**。`Bus` 遵循同一规则，返回 `null` 而不是构造 —— `TickableBusTests.BusIsNullForAChannelThatWasNeverStarted` 断言了它，并注明查询不得把创建通道当作副作用。

## 注册表

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 1019-1032 行）
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

工厂有两点承重：

- **转发在工厂内部**，所以无论多少线程竞争 `GetOrCreateChannel`，每个名字恰好接线一次。没有订阅者簿记、没有退订路径、没有重复触发。
- **通道永不移除。** `ChannelNames` 公开一个只增不减列表的键。没有 `CloseChannel`；`StopAsync` 停住泵并保留传输，这正是 `RestartAsync` 与「重启复用同一条 bus」得以成立的原因。

注册表还赋予了事件继承的进程范围语义。`_channels` 是 `static`、事件也是 `static`，所以一次订阅会收到所有通道的事件 —— 载荷里的通道名是唯一区分手段，sender 是 `LoopChannel`（私有类型）而不是 `TickManager`。

## 发布-订阅

`LoopChannel` 触发自己的实例事件；门面用新载荷重新触发。链路是：泵或修改器 → `LoopChannel` 实例事件 → 静态转发 lambda → `TickManager` 静态事件 → 所有订阅者。

| 迁移 | 触发者 | 抑制它的事件 |
|---|---|---|
| Started | `LoopChannel.Start`，末尾 | 开头的 `if (_isRunning) return;` —— 重复 `Start` 不触发 |
| Paused | `LoopChannel.Pause` | `if (!_isRunning \|\| _bus.IsPaused) return;` |
| Resumed | `LoopChannel.Resume` | `if (!_isRunning \|\| !_bus.IsPaused) return;` |
| Stopped | `LoopChannel.StopAsync`，末尾 | 开头的 `if (!_isRunning) return;` |

这个模式*只对真实迁移诚实*：每个处理器都放在保护之后，所以事件意味着状态确实变了。`TogglePause` 不可能同时触发两者，因为它调用 `Pause` 或 `Resume`，而这两者是唯一的触发点。

订阅者应据此设计的两点：

- 处理器运行在调用者线程上 —— `Start` / `Pause` / `Resume` / `TogglePause` 是调用线程；`StopAsync` / `RestartAsync` 末尾是 awaiter 的续体上下文。调用没有保护，抛异常的处理器会传播给调用方；此时循环已经在跑或已经停下，所以不受影响。
- 示例**不**订阅这些事件，而是轮询（`MainWindow.xaml.cs` 第 142-154 行）。理由写在文件里：钩子里调用 `Dispatcher.Invoke` 会被引擎的按钩子捕获吞掉，所以示例发布不可变快照，让 UI 线程读取。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 276-330 行（Start）、331-377（StopAsync）、386-404（Pause/Resume）、1019-1044（注册表与事件）、1109-1156（查询）；`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs` 第 142-154 行；`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` 第 112-131 行。
