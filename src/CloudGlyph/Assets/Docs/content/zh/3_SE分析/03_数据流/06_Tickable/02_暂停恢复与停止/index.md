# 暂停、恢复与停止

这些迁移在不拆除通道的前提下停止并重新开始交付。流程不长，但状态很多：暂停活在共享时钟上，停止必须触达 park 住的泵，重启必须重新锚定时钟。

```plantuml
@startuml
!theme plain

actor Caller as Caller
participant "TickManager\n(静态门面)" as TM
participant "LoopChannel\n(私有引擎)" as Ch
participant "ITimeSourceControl\n(总线)" as Bus
participant "Update 泵\n(线程，park 或运行)" as UT
participant "FixedUpdate 泵\n(线程，park 或运行)" as FT

== 暂停 ==
Caller -> TM: Pause("demo")
activate TM
TM -> Ch: Pause()
activate Ch
alt 未运行，或已暂停
    Ch --> TM: return - 无状态变化、无事件
else 运行中且未暂停
    Ch -> Bus: Pause()
    Ch --> TM: Paused
end
deactivate Ch
TM -> TM: OnChannelPaused?.Invoke(s, new TickChannelEventArgs("demo"))
deactivate TM

UT -> Bus: IsAdvancing
Bus --> UT: false
UT -> Bus: WaitWhileStalledAsync(token)
note right of UT: park 在这里 - 不轮询、不唤醒
FT -> Bus: WaitWhileStalledAsync(token)
note right of FT: 两条泵 park 在同一个信号上

== 恢复 ==
Caller -> TM: Resume("demo")
activate TM
TM -> Ch: Resume()
activate Ch
alt 未运行，或未暂停
    Ch --> TM: return
else 运行中且已暂停
    Ch -> Bus: Resume()
    note right of Bus: 若速率为 0，这只解除暂停，时钟仍\n永不前进 - 只有非零速率能重新启动它
    Ch --> TM: Resumed
end
deactivate Ch
TM -> TM: OnChannelResumed?.Invoke(s, new TickChannelEventArgs("demo"))
deactivate TM

== StopAsync ==
Caller -> TM: StopAsync("demo")
activate TM
TM -> Ch: StopAsync()
activate Ch
alt 未运行
    Ch --> TM: return - 不触发 OnChannelStopped
else 运行中
    Ch -> Ch: _isRunning = false
    Ch -> Ch: _isUpdateThreadActive = false; _isFixedUpdateThreadActive = false
    Ch -> Bus: Resume()
    note right of Bus: 停止不能把暂停留给下一个生命周期
    Ch -> Ch: _cts.Cancel()
    alt 异步循环模式
        Ch -> UT: await Task.WhenAny(Task.WhenAll(pending), Task.Delay(1000))
        Ch -> FT: （同样的等待）
    else 线程模式
        Ch -> UT: Join(1000)
        Ch -> FT: Join(1000)
    end
    Ch -> UT: WaitWhileStalledAsync 观察到令牌并返回
    Ch -> Ch: ResetStatistics()
    Ch -> Ch: ClearQueues()
    note right of Ch: 新增、移除、配置与主线程队列全部排空。\n停止期间到达的注册会丢失。
    Ch --> TM: Stopped
end
deactivate Ch
TM -> TM: OnChannelStopped?.Invoke(s, new TickChannelEventArgs("demo"))
deactivate TM

== RestartAsync ==
Caller -> TM: RestartAsync("demo")
activate TM
TM -> Ch: RestartAsync()
activate Ch
Ch -> Ch: await StopAsync()
Ch -> Ch: WaitForConditionAsync(!running && !threadsActive, 1000, 5)
alt 关闭未确认
    Ch -> Ch: ForceCleanup()
    note right of Ch: 取消并释放 CTS、清空线程字段、清空队列
end
Ch -> Ch: WaitForConditionAsync(四个队列全空, 500, 2)
Ch -> Ch: Start()
Ch --> TM: done
deactivate Ch
TM -> TM: OnChannelStarted?.Invoke(...)
deactivate TM

@enduml
```

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 331-377 行（StopAsync）、386-404（Pause/Resume）、406-432（RestartAsync）、444（TogglePause）、956-995（ClearQueues、ForceCleanup、WaitForConditionAsync）、1053-1066（静态转发）。

## 为什么 park 住的泵仍能被停止

这是设计必须解决的失败模式，固定它的测试是 `TickableBusTests.StoppingWhilePausedEndsTheChannel`：

> 停摆中的循环 park 在一个对令牌一无所知的等待上。不在这个等待里观察令牌的话，`StopAsync` 会一直等下去，然后 `ForceCleanup` 释放掉那个令牌源，异常从线程体里逃出去。

防止这种情况的契约在 `WaitWhileStalledAsync` 上 —— 它接受令牌，所以取消会传播*进* park。测试断言任务对 5 秒超时获胜。

## 每个迁移重置什么，不重置什么

| | `Pause` | `Resume` | `StopAsync` | `RestartAsync` |
|---|---|---|---|---|
| `_isRunning` | 不变 | 不变 | `false` | 先 `false` 后 `true` |
| bus 暂停标志 | `true` | `false` | `false`（清除） | 清除后不变 |
| bus 速率 | 不变 | 不变 | **不**清除 | **不**清除 |
| `TotalFrames` / `TotalTime` / `CurrentFPS` | 不变 | 不变 | 归零 | 重置后重新累计 |
| 行为注册 | 不变 | 不变 | **已应用的存活**；排队的丢弃 | **已应用的存活**；排队的丢弃 |
| 重跑 `Awake` / `Start` | 否 | 否 | 否 | **否** |
| 采样器 | 不变 | 不变 | 不变 | **重新锚定** |
| 触发事件 | `OnChannelPaused` | `OnChannelResumed` | `OnChannelStopped` | `OnChannelStopped` + `OnChannelStarted` |

表中有三条一旦忽略就会出问题：

- **速率 `0` 不是 bus 的暂停标志，`Resume` 与 `StopAsync` 都不清除它。** `SetTimeScale(0)` 冻结时钟；`StopAsync` 的 `_bus.Resume()` 只解除*暂停*。速率 0 下停止的通道会重启并立刻再次 park。示例把 `IsAdvancing` 打印在 `SystemStatus` 旁边，就是为了让两种状态在屏幕上可区分（`MainWindow.xaml.cs` 第 276-285 行）。
- **`StopAsync` 排空注册队列，但不清空已应用的注册。** `ClearQueues` 丢弃仍在 `_addQueue` 或 `_removeQueue` 中的行为；`_behaviors` 字典原封不动，所以已经排空过的行为在下次 `Start` 后继续被驱动 —— 且不重跑 `Awake` / `Start`。期望停止后行为脱离的宿主必须调用 `CloseTickable()` *并让移除操作在停止前排空*（或在重启后重新注册）。
- **`RestartAsync` 也不重跑 `Awake` / `Start`。** 唯一会重跑的路径是 `CloseTickable()` + `InitializeTickable()`。

## 保护的位置让事件诚实

每个处理器都写在保护*之后*，从不在之前。所以事件意味着「状态确实变了」，而保护定义了哪些迁移是静默的：

| 调用 | 何时被抑制 | 触发 |
|---|---|---|
| `Pause` | 未运行，或已暂停 | `OnChannelPaused` |
| `Resume` | 未运行，或未暂停 | `OnChannelResumed` |
| `TogglePause` | 未运行 | 上面两者之一，恰好一个 |
| `StopAsync` | 未运行 | `OnChannelStopped` |
| `Start` | 已在运行 | `OnChannelStarted` |

`TogglePause` 不可能两者都触发，因为它就是 `if (_bus.IsPaused) Resume(); else Pause();`（第 444 行），而这两个方法是唯一的触发者。

## 失败与边界路径

- **暂停中停止。** 见上，正常完成。
- **fixed 泵正在批次中间时停止。** 派发循环在每个行为顶部检查令牌（中断条件里的 `token.IsCancellationRequested`），所以长批次会在一个行为之内中止。
- **队列非空时停止。** `ClearQueues` 在 `finally` 块中排空四个队列，所以从未应用的注册与注销会被丢弃，而不是泄漏进下一个生命周期。
- **关闭未确认后重启。** `ForceCleanup` 是回退：取消并释放令牌源、清空线程与任务字段、清空队列。这是唯一可能在下次 `Start` 创建新泵时旧泵仍在运行的路径，所以它会向 `Debug.WriteLine` 写警告。
- **`RestartAsync` 的排空等待是尽力而为。** 它的 `WaitForConditionAsync` 结果被忽略；若 500 ms 后队列仍非空，`Start` 照常进行（`TickManager.cs` 第 422-427 行）。
- **`StopAsync` 永不 fault。** 泵的 join 包在 `try { … } catch (Exception) { }` 中，清理在 `finally`，所以即使泵失常，返回的任务也成功完成。
