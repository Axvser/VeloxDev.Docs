# 数据流 — 过渡动画：节拍与编组

每帧发生两件事：循环决定*何时*采样（节拍），以及每次采样的值在目标自己的线程上写入（编组）。它们是关注点不同、失败模式也不同的两件事，因此分开画。

## (a) 一趟：时间轴驱动的采样

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

> 源：`Src/Core/VeloxDev.Core/TransitionSystem/Runtime/TransitionInterpreter.cs`（`ExecuteSamplingLoopAsync`、`RunPassAsync`、`EmitFrame`、`ArmNextFrame`）、`FramePacerCore.cs`、`ReusableTimerWait.cs`、`TransitionRun.cs`。

承重的一行是 `run.PassAnchor = timeline.Ticks`。一趟是绝对时间轴上的**锚点**，绝不是重置 —— 因此多个运行可以共享一个源（各自保留自己的趟与位置），而 `Transition.Seek` 不过是写入另一个锚点。图里显示两个后果：一趟只在唯一位置结束（它的远端），因为时间轴只向前走；且一趟的最后一帧是**精确**端点（正向 `easedT = 1`、反向 `0`），与 `Ease(1)` 是否精确为 `1` 无关。

`FPS` 值得重申：它是*上限*，不是栅格。`ArmNextFrame` 每帧重读 `1000 / max(1, FPS)`，因此在运行中的动画上收紧上限会立即生效；晚醒只是画出更靠后的一帧。

## (b) 等待：宿主节拍器，否则一个复用的定时器

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

> 源：`Src/Core/VeloxDev.Core/TransitionSystem/Runtime/{FramePacerCore,ReusableTimerWait,TransitionInterpreter}.cs`、`Src/Adapters/*/PlatformAdapters/TransitionInterpreter.cs`。

为什么自定义 awaiter 不被编组回去：`FrameWait` 实现 `INotifyCompletion`，刻意**不**实现 `ICriticalNotifyCompletion`，因此构建器会流动调用方的 `ExecutionContext` —— 但恢复 `SynchronizationContext` 是 `Task` 的职责，所以自定义 awaiter 的续体在完成等待的任意线程上恢复。因此，在 UI 线程上启动的循环会在第一帧后漂到线程池线程，*除非宿主提供了节拍器*。这就是节拍接缝存在的全部理由，也是宿主必须从与写路径相同的答案推导节拍器的原因：与 `Post` 不一致的节拍器会把每一帧变成一次派发。

## (c) UI 线程跳跃

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
          and it is reported once through Warn(WarnStage.Dropped).
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

> 源：`Src/Core/VeloxDev.Core/TransitionSystem/Sampling/SamplerSet.cs`（`Apply`、`ApplyCore`、缓存闭包、`SetRun`）、`Src/Core/VeloxDev.Core/Threading/ThreadDispatcherBase.cs`、`Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`。

这个流程中有三个避免分配的决定：

- **缓动时间放在字段里，不是闭包里。** `Apply` 为每个目标保留一个缓存 `Action`，并用 `Interlocked.Exchange(ref _cachedTimeBits, BitConverter.DoubleToInt64Bits(t))` 存 `t`，因此每次采样编组零分配。
- **线程不逐帧重新推导。** 运行在调度器启动它时一次性钉住自己的 `ThreadRef`，因为写路径跑在采样循环的线程上，而那个线程对一个「答案取决于调用方」的宿主（Blazor 回路的 renderer）给不出答案。
- **检查在排队写入内部重复。** `ApplyCore` 重新检查 token 与存活标志，因为写入发生在消息被泵送时，而动画可能已在中间被取消；只在排队前检查会让已经过期的帧覆盖一次重置。
