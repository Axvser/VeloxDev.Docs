# 数据流 — Tickable

tickable 特性有一条包含三个阶段的调用链；按顺序阅读，因为每一阶段都改变下一阶段依赖的状态：

1. **启动与注册** —— 调用方启动通道并把行为入队；update 泵在采样之前排空队列，所以 `Awake` 与 `Start` 落在第一个 `Update` 之前。
2. **帧交付** —— 稳态：一次 `Update` 扫描、一次 `LateUpdate` 扫描，以及另一线程上独立的 `FixedUpdate` 批次。
3. **暂停、恢复与停止** —— 不拆除通道就停止并重新开始交付的迁移。

## 整个生命周期一张图

```plantuml
@startuml
!theme plain

actor Caller as Caller
participant "Tickable\n(用户类)" as Beh
participant "TickManager\n(静态门面)" as TM
participant "LoopChannel\n(私有引擎)" as Ch
participant "ITimeSourceControl\n(总线)" as Bus
participant "Update 泵\n(线程)" as UT
participant "FixedUpdate 泵\n(线程)" as FT

== 启动 ==
Caller -> Beh: InitializeTickable()
activate Beh
Beh -> TM: RegisterBehaviour(this, "demo")
activate TM
TM -> Ch: GetOrCreateChannel("demo")
TM -> Ch: RegisterBehaviour(behavior)
Ch -> Ch: _addQueue.Enqueue(behavior)
deactivate TM
deactivate Beh

Caller -> TM: Start("demo")
activate TM
TM -> Ch: Start()
activate Ch
Ch -> Bus: Resume()
Ch -> Ch: _updateSampler.Reset() / _fixedSampler.Reset()
Ch -> Ch: RebuildCachedWrappers()
Ch -> FT: new Thread(FixedUpdateLoop).Start()
Ch -> UT: new Thread(UpdateLoop).Start()
Ch --> TM: Started
deactivate Ch
TM -> TM: OnChannelStarted?.Invoke(new TickChannelEventArgs("demo"))
deactivate TM

== 注册排空（update 泵，首次采样之前） ==
UT -> Ch: ProcessMainThreadOperations()
activate Ch
Ch -> Ch: ProcessAddedBehaviors()
Ch -> Beh: InvokeAwake()
Ch -> Beh: InvokeStart()
Ch -> Ch: _wrappersNeedSort = true
deactivate Ch

== 稳态 ==
loop 每帧直到停止
    UT -> Bus: IsAdvancing
    alt 时钟停摆
        UT -> Bus: WaitWhileStalledAsync(token)
    else 时钟推进
        UT -> Ch: ProcessMainThreadOperations()
        UT -> Ch: _updateSampler.Sample()
        UT -> Beh: InvokeUpdate(frameArgs)
        alt Handled 已置位
            UT -> UT: break - 跳过整个 LateUpdate 扫描
        end
        UT -> Beh: InvokeLateUpdate(frameArgs)
        UT -> Ch: _frameEventArgsPool.Return(frameArgs)
        UT -> Ch: FrameRateControlSync()
    end
end

loop 每个欠下的步，在自己的线程上
    FT -> Bus: IsAdvancing
    alt 时钟停摆
        FT -> Bus: WaitWhileStalledAsync(token)
    else 时钟推进
        FT -> Ch: _fixedSampler.Advance(out sample)
        FT -> Beh: 对每个欠步调用 InvokeFixedUpdate(stepArgs)
    end
end

== 暂停与恢复 ==
Caller -> TM: Pause("demo")
activate TM
TM -> Ch: Pause()
Ch -> Bus: Pause()
Ch --> TM: Paused
TM -> TM: OnChannelPaused?.Invoke(...)
deactivate TM
note right of Bus: 两条泵都 park 在这里 —— IsAdvancing 现在为 false

Caller -> TM: Resume("demo")
activate TM
TM -> Ch: Resume()
Ch -> Bus: Resume()
Ch --> TM: Resumed
TM -> TM: OnChannelResumed?.Invoke(...)
deactivate TM

== 停止 ==
Caller -> TM: StopAsync("demo")
activate TM
TM -> Ch: StopAsync()
activate Ch
Ch -> Ch: _isRunning = false
Ch -> Bus: Resume()
Ch -> Ch: _cts.Cancel()
Ch -> UT: join（超时 1000 ms）
Ch -> FT: join（超时 1000 ms）
Ch -> Ch: ResetStatistics() / ClearQueues()
Ch --> TM: Stopped
deactivate Ch
TM -> TM: OnChannelStopped?.Invoke(...)
deactivate TM

@enduml
```

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 276-330 行（Start）、331-377（StopAsync）、386-404（Pause/Resume）、432-440（注册）、511-556（UpdateLoop）、448-509（FixedUpdateLoop）、755-803（排空）、1019-1032（GetOrCreateChannel）、1050-1072（静态转发）。

## 按阶段划分的流程

| 子页 | 流程 | 图 |
|---|---|---|
| [启动与注册](00_启动与注册/index.md) | `InitializeTickable()` → `RegisterBehaviour` → `GetOrCreateChannel` → `Start` → 排空 → `InvokeAwake`/`InvokeStart` | PlantUML |
| [帧交付](01_帧交付/index.md) | 每帧 `InvokeUpdate` → `InvokeLateUpdate`、`Handled` 短路、并发的 `InvokeFixedUpdate` 批次，以及异常路径 | PlantUML |
| [暂停恢复与停止](02_暂停恢复与停止/index.md) | `Pause` / `Resume` / `TogglePause` / `StopAsync` / `RestartAsync`，包括 park 泵与暂停中停止的路径 | PlantUML |

## 什么跨过哪条边界

上面的流程只有在线程边界明确时才有意义。图中每个箭头都跨过四种边界之一：

| 从 → 到 | 机制 | 后果 |
|---|---|---|
| 调用方 → `LoopChannel` | `ConcurrentQueue<T>`（新增、移除、配置）或 `volatile` 字段 | 无锁；稍后应用，不在调用时 |
| Update 泵 → 行为 | 直接方法调用 | 同步；慢钩子会推迟该帧 |
| FixedUpdate 泵 → 行为 | 在自己的线程上直接方法调用 | 与 Update 并发；共享状态需自行加锁 |
| 泵 → bus | `ITimeSourceControl` | 暂停与速率被两条泵、以及同一时钟上的动画共同观察 |

这条链中**没有**的是任何向 UI 线程的封送。`ExecuteOnMainThread` 的目标是 update 泵，而在钩子里阻塞等待 `Dispatcher.Invoke` 会被按钩子的异常保护捕获。
