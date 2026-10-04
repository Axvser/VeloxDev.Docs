# 数据流 — 过渡动画：运行生命周期

一次 `Execute` 调用，从流式构建器到最后一帧。独特的一步是 `Prepare`：解释器从不触碰已声明状态，只碰 `Prepare` 产出的那套 `SamplerSet`，而那套集合就是本引擎里「状态快照」的含义 —— 每条已声明路径一条条目，各持有它的采样器加上两个**归一化端点值**。

## (a) 一趟、一个分段

```plantuml
@startuml
!theme plain

actor "Caller" as Caller
participant "Transition<T>\n(builder + chain)" as SS
participant "TransitionScheduler" as Sch
participant "Host\n(ITransitionHost)" as Host
participant "InterpolatorCore" as IC
participant "SamplerSet" as SET
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target" as TGT

Caller -> SS: Execute(target, CanMutualTask)
activate SS

SS -> SS: walk root -> next;\nqueue (interpolator, delay, effect-clone, state) per segment
SS -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch --> SS: the shared scheduler from MutualSchedulers (per-target cache)
    SS -> Sch: DrainActive()  (supersede the running mutual run)
else CanMutualTask == false
    Sch --> SS: a fresh scheduler, registered in NoMutualSchedulers
end
deactivate Sch

SS -> SS: new TransitionRun(runSource)\nTrack(run); add no-mutual registration if concurrent
SS -> Sch: Execute(interpolator, state, effect, cts)
activate Sch
Sch -> Sch: await _gate  (serialize executions on this scheduler)
Sch -> Host: PostAsync(target, () => effect.InvokeAwake(target, args))
activate Host
Host -> EF: Awaked
Host --> Sch: accepted true, or false when the queue refused it
deactivate Host

note right of Sch
  Awake is awaited, not fired and forgotten:
  it may veto the run (Args.Handled) and may put
  the target into the state the segment starts from,
  so Prepare must not read the target until it has run.
  A refused dispatch aborts here with a Warn.
end note

Sch -> IC: Prepare(target, state, effect, host)
activate IC
loop every declared path
    IC -> IC: bound = property.BindTo(target)  (freeze PathIndex.Frozen args)
    IC -> Host: Run(target, () => bound.GetValue(target))
    activate Host
    Host --> IC: current value, or TransitionProperty.UnreadablePath
    deactivate Host
    IC -> IC: resolve sampler:\nstate override -> registry (exact, base classes, interfaces)\n-> struct ISampleable (StructAssembler)
    IC -> IC: normStart = NormalizeStart(cur, new, opt)\nnormEnd = NormalizeEnd(cur, new, opt)
    IC -> SET: Add(bound, sampler, normStart, normEnd, options)
end
IC --> Sch: SamplerSet (one entry per path)
deactivate IC

alt Awake vetoed, cts cancelled, or the generation changed
    Sch --> SS: no sampling
else
    Sch -> SET: SetRun(run)   (timeline + pass the frames are positioned against)
    Sch -> TI: Execute(target, samplerSet, effect, cts)
    activate TI
    TI -> TI: sampling loop  (see the pacing page)
    TI --> Sch: completed or cancelled
    deactivate TI
end
Sch -> Sch: finally: release _gate
Sch --> SS: return the frame set (ExecuteCapturing) or nothing (Execute)
deactivate Sch

SS -> SS: finally (after the last segment):\nUntrack(run); remove no-mutual registration; run.Dispose()
SS --> Caller: return (the call returns before the animation finishes)
deactivate SS
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Transition.cs`（`CoreExecute`、`ExecuteCoreAsync`、`RunSegmentAsync`）、`TransitionScheduler.cs`（`FindOrCreate`、`ExecuteCore`、门、代计数器、`Track`/`Untrack`）、`Interpolator.cs`（`Prepare`）、`SamplerSet.cs`。

## (b) 已准备状态是什么

`Prepare` 是唯一读目标的地方。下游一切都从产出的 `SamplerSet<TPriorityCore>` 工作，其条目恰是 `(property, sampler, normalizedStart, normalizedEnd, options)` 外加一份惰性创建的 `working` 暂存：

```plantuml
@startuml
!theme plain

participant "CoreExecute" as SS
participant "Prepare" as P
participant "state (IFrameState)" as ST
participant "SamplerSet" as SET
participant "Interpreter" as TI

SS -> P: Prepare(target, state, effect, host)
activate P
P -> P: diagnostics = new TransitionDiagnostics(effect, target)
loop path p in state.Values
    alt state.Interpolators holds p
        P -> P: sampler = the per-property override
    else registry resolves p.PropertyType
        P -> P: sampler = TryGetInterpolator(p.PropertyType)
    else p is a value type implementing ISampleable
        P -> P: sampler = StructAssembler.Create(...)  (null means skip)
    else
        P -> P: Warn("Unsampled") and skip this path
    end
    P -> ST: TryGetOptions(p)
    ST --> P: options (e.g. RotationDirection)
    P -> P: normStart = sampler.NormalizeStart(cur, new, options)\nnormEnd = sampler.NormalizeEnd(cur, new, options)
    P -> SET: Add(property, sampler, normStart, normEnd, options)
end
P --> SS: the set
deactivate P
SS -> TI: Execute(target, set, effect, cts)
activate TI
TI -> SET: Apply(target, easedT, priority)   per frame
activate SET
SET -> SET: skip when cancelled or the host is dead
SET --> TI: (each entry writes through its sampler)
deactivate SET
deactivate TI
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`（`Prepare<TPriorityCore>`）、`SamplerSet.cs`（`Add`、`Apply`、`CanSetValue`）、`StructAssembler.cs`。

关于这套集合、让引擎其余部分保持简单的三个事实：

- **它对整趟是固定的。** 已声明值与采样器只解析一次；一帧永不重读 state、重解析路径或重解析类型。这就是 `Repeat` 能*重放*它首次迭代准备的那套集合、且每次都得到完全相同动画的原因。
- **端点已经归一化。** `NormalizeStart` / `NormalizeEnd` 已用起点值、终点值与 options 跑过一次；帧路径只是拿一个缓动时间去求值。
- **准备不成的路径被跳过，而非致命。** `UnreadablePath`（路径不匹配此目标的运行时类型）与「解析不出采样器」都产出一条 `Warn` 与一条缺失条目 —— 集合其余部分照常动画。`StructAssembler` 返回 `null` 是同一结果。唯一*确实*致命的情形发生在更早，在 `Execute` 中同步发生：一条声明为引用类型、什么都解析不出的路径抛 `TransitionPathUnsampleableException`。

## (c) 分段串联与循环

```plantuml
@startuml
!theme plain

participant "CoreExecute" as SS
participant "DelayWhilePausedAsync" as D
participant "Scheduler\n(chainScheduler)" as Sch
participant "prepared[]" as PP

SS -> SS: segments[] and repeats[] built by walking root -> next
SS -> SS: prepared[] = new SamplerSet[segments.Count]

note over SS
  RunRangeAsync(from, to) expands the loop of segment `to`
  (a segment's loop wraps the chain from its FIRST segment
  through that one, and loops nest by where they end)
end note

loop for each iteration of the innermost loop, innermost last
    SS -> D: DelayWhilePausedAsync(run.Timeline, segment.Delay, cts)
    activate D
    D -> D: park while paused; measure the delay on the WALL clock
    D --> SS: delay consumed, or OperationCanceledException
    deactivate D
    alt prepared[i] is null   (first iteration of this segment)
        SS -> Sch: ExecuteCapturing(interpolator, state, effect, cts)
        activate Sch
        Sch --> SS: the ready SamplerSet, stored into prepared[i]
        deactivate Sch
    else
        SS -> Sch: Replay(prepared[i], effect, cts)
        note right of Sch
          A replay re-reads nothing and re-raises no Awake;
          Start / Update / LateUpdate / Completed and the
          diagnostics still fire, exactly like a pass.
        end note
    end
end

SS -> SS: finally: Untrack(run); remove the no-mutual registration; run.Dispose()
@enduml
```

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Transition.cs`（`RunSegmentAsync`、`RunBodyAsync`、`RunRangeAsync`、`DelayWhilePausedAsync`）、`TransitionScheduler.cs`（`ExecuteCapturing`、`Replay`）。

分段之间的延时按**墙钟**（一个 `Stopwatch`）测量，不按源：速率为零会冻结源却不暂停它（`IsPaused` 仍为 false），而在冻结时钟上测量的延时永远减不下去。采样循环刻意相反 —— 它用时间轴，因为在那里时间轴才决定动画走了多远。
