# 数据流 — 过渡动画：节拍与编组

每帧发生两件事：循环决定*何时*采样（节拍），以及每个样本的值被写到目标自己的线程上（编组）。它们是两件各有失败模式的事，因此分开绘制。

## (a) 一趟：由时间轴驱动的采样

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "FramePacerCore\n(host pacer or none)" as PACER
participant "ReusableTimerWait\n(default wait)" as WAIT
participant "Run" as RUN
participant "Timeline\n(ITimeSourceControl)" as TL
participant "Effect" as EF

TI -> EF: InvokeStart(sender, args)  (once per run)
TI -> TI: run = frameSet.Run\nforeverloop = (LoopTime == int.MaxValue)\nstartCycle = run.Cycle

note over TI
  The run and the start-cycle offset are what make a
  segment's loop its OWN: a second segment in a chain
  begins with the shared counter already advanced.
end note

loop while foreverloop or run.Cycle - startCycle <= LoopTime
    TI -> RUN: PassAnchor = Timeline.Ticks  (an anchor, not a reset)
    loop forward pass until rawT >= 1
        alt cts cancelled or Args.Handled
            TI -> TI: throw OperationCanceledException
        else timeline is not advancing
            TI -> TI: draw the frozen position ONCE
            TI -> TL: await WaitWhileStalledAsync(cts.Token)
            note right of TI
              Draw-then-park is what makes a seek while paused
              visible without resuming: the wait is replaced by
              a nudge, so the loop wakes, draws and parks again.
              A plain pause therefore costs one frame and then
              NO timer wake-ups at all.
            end note
        else
            TI -> TL: elapsedTicks = Ticks - PassAnchor
            TI -> TI: rawT = TicksToMs(elapsedTicks) / durationMs\neasedT = rawT >= 1 ? 1 : Ease.Ease(rawT)
            TI -> EF: InvokeUpdate
            TI -> TI: apply(easedT)  into SamplerSet.Apply  (see part b)
            TI -> EF: InvokeLateUpdate
            alt host supplied a pacer
                TI -> PACER: Schedule(continuation, 1000 / max(1, FPS) ms, token)
            else
                TI -> WAIT: Schedule(continuation, 1000 / max(1, FPS) ms, token)
            end
            note over TI, WAIT
              Interval is re-read per frame, so raising FPS mid-animation
              tightens the cap. The interval only caps how OFTEN the loop
              looks; the timeline decides how FAR the frame is.
            end note
        end
    end
    opt IsAutoReverse
        loop backward pass until rawT >= 1
            TI -> TI: easedT = rawT >= 1 ? 0 : Ease.Ease(1 - rawT)
        end
    end
    TI -> RUN: NextCycle()
end
TI -> EF: InvokeCompleted(sender, args)
TI -> EF: InvokeFinally(sender, args)
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs`（`ExecuteSamplingLoopAsync`、`RunPassAsync`、`EmitFrame`、`ArmNextFrame`）、`FramePacerCore.cs`、`ReusableTimerWait.cs`、`TransitionRun.cs`。

承重的一行是 `Pacer.PassAnchor = Timeline.Ticks`。一趟是绝对时间轴上的一个**锚点**，绝不是重置 —— 因此多个 run 能共享一个源（各自保留自己的趟与位置），而 `Transition.Seek` 不过是写入一个不同的锚点。图里显示的两个后果：一趟恰在一个地方结束（它的远端），因为时间轴只向前走；一趟的最后一帧是**精确**端点（正向 `easedT = 1`、反向 `0`），与 `Ease(1)` 是否恰为 `1` 无关。

`FPS` 值得重申：它是*上限*，不是栅格。`ArmNextFrame` 每帧重读 `1000 / max(1, FPS)`，因此在运行中的动画上收紧上限会立即生效；醒晚了只是画出一帧走得更远的画面。

## (b) 等待：宿主节奏器，否则一个复用定时器

```plantuml
@startuml
!theme plain

participant "Interpreter" as TI
participant "FramePacerCore" as P
participant "Host timer\n(DispatcherTimer etc.)" as T
participant "ReusableTimerWait" as W
participant "Timer\n(thread pool)" as TP

TI -> TI: ArmNextFrame(continuation, interval, token)
alt token already cancelled
    TI -> TI: run the continuation now (a stop costs no interval)
else the host resolved a pacer on the first frame
    TI -> P: Schedule(continuation, interval, token)
    activate P
    P -> P: Volatile.Write(_pending, continuation)  -- BEFORE arming
    P -> T: Arm(interval)   (subclass hook)
    activate T
    T --> P: tick  ->  pacer.Fire()
    deactivate T
    P -> P: Disarm() first, then Interlocked.Exchange(_pending, null)
    P --> TI: continuation runs ON the host's thread
    deactivate P
else
    TI -> W: Schedule(continuation, interval, token)
    activate W
    W -> W: bind the token once for the whole loop
    W -> TP: Change(interval, infinite)
    activate TP
    TP --> W: callback  ->  Fire()
    deactivate TP
    W --> TI: continuation runs on a thread-pool thread
    deactivate W
end

note over P, W
  Publishing before arming, and disarming before invoking,
  are both ordering constraints: an already-expired timer must
  not tick before the continuation is attached, and a repeating
  wait must not complete again before the loop armed the next frame.
end note
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/{FramePacerCore,ReusableTimerWait,TransitionInterpreter}.cs`、`Src/Adapters/*/PlatformAdapters/TransitionInterpreter.cs`。

自定义 awaiter 为何不被编组回来：`FrameWait` 实现 `INotifyCompletion` 且刻意**不**实现 `ICriticalNotifyCompletion`，于是 builder 会把调用方的 `ExecutionContext` 流下去 —— 但恢复 `SynchronizationContext` 是 `Task` 的活，所以自定义 awaiter 的续体在哪个线程上完成等待就在哪个线程上恢复。因此一个在 UI 线程上启动的循环，除非宿主提供了节奏器，会在第一帧之后漂到线程池线程上。这正是节奏接缝存在的全部理由，也是宿主必须从写路径所用的同一答案推出节奏器、否则与 `Post` 不一致的节奏器会把每一帧变成一次派发的原因。

## (c) UI 线程跳转

```plantuml
@startuml
!theme plain

participant "Interpreter" as TI
participant "SamplerSet" as SET
participant "Host\n(ITransitionHost)" as H
participant "ISampler" as SM
participant "Target" as TGT

TI -> SET: Apply(target, easedT, priority)
activate SET
alt cts.IsCancellationRequested
    SET --> TI: return  (a stale queued frame is discarded)
else host.IsAlive is false
    SET --> TI: return  (no write, no further frames)
else
    SET -> SET: resolve the thread the RUN is pinned to\n(fall back to host.ThreadFor(target) with no run)
    SET -> H: Post(target, thread, cachedApply, priority)
    activate H
    alt the caller is already on that thread
        H -> H: RunInline(cachedApply)   -- no dispatch at all
    else
        H -> H: PostCore(target, thread, action, priority)
        note right of H
          Returns false when nothing was queued at all
          (dispatcher gone, or no queue yet). That is the only
          way a caller can tell a dropped action from a queued one,
          and it is reported once through Warn("Dropped").
        end note
    end
    H -> SM: InsertFrame(target, property, ref working, start, end, options, t)
    SM -> TGT: write the value (endpoints written exactly)
    deactivate H
    note right of SET
      The cancellation and liveness checks are repeated inside
      the queued write, so a frame that landed after a reset
      is discarded too.
    end note
    SET --> TI: return
end
deactivate SET
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/SamplerSet.cs`（`Apply`、`ApplyCore`、缓存闭包、`SetRun`）、`Src/Core/VeloxDev.Core/Threading/ThreadDispatcherBase.cs`、`Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`。

这条流里有三个避免分配的决定可见：

- **缓动时间经字段而不是闭包传递。** `Apply` 为每个目标保留一个缓存的 `Action`，并用 `Interlocked.Exchange(ref _cachedTimeBits, BitConverter.DoubleToInt64Bits(t))` 存 `t`，因此每采样编组零分配。
- **线程不逐帧重新推导。** 一趟在调度器启动它时把 `ThreadRef` 钉死一次，因为写路径跑在采样循环的线程上，而那个线程对一个「答案取决于调用方」的宿主没有答案 —— 例如从那里无法命名 Blazor 回路的 renderer。
- **检查在已排队的写入内部重复。** `ApplyCore` 重新检查 token 与存活标志，因为写入发生在消息被泵送时，而动画可能在这中间被取消；只在排队前检查会让一个已经过期的帧覆盖一次重置。
