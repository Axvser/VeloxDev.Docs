# 数据流 — 过渡动画

## (a) 正常执行流

从 `snapshot.Execute(target)` 到 Stopwatch 驱动采样循环的完整调用链。此流程在全部六个平台适配器上一致运行。

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "InterpolatorCore" as IC
participant "UIThreadInspector" as UI
participant "SamplerSet" as FUS
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target (UI element)" as T

User -> SS: Execute(Rec0, CanMutualTask)
activate SS

SS -> TC: (static) Execute(target, snapshot, CanMutualTask)
activate TC

TC -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch -> Sch: return shared mutual scheduler (ConditionalWeakTable)
else CanMutualTask == false
    Sch -> Sch: return one-off non-mutual scheduler
end
Sch --> TC: scheduler
deactivate Sch

TC -> Sch: Execute(producer, state, effect, cts)
activate Sch

Sch -> IC: Prepare(target, state, effect, inspector)
activate IC

loop every recorded property
    IC -> UI: ProtectedGetValue(target, property)  (marshalled if needed)
    UI --> IC: currentValue (start)
    alt custom sampleable (state.Interpolators)
        IC -> IC: sampleable = state.Interpolators[property]
    else registry TryGetInterpolator(propertyType)
        IC -> IC: sampleable = NativeInterpolators[type]
    else current/new value is ISampleable
        IC -> IC: sampleable = value
    end
    IC -> IC: sampler = sampleable.Normalize(current, new, options)
    IC -> FUS: Add(property, sampler, current, new, options)
end

IC --> Sch: SamplerSet (one prepared sampler per property)
deactivate IC

Sch -> TI: Execute(target, samplerSet, effect, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start event fired

loop each pass (forward; backward when IsAutoReverse)
    loop sample until rawT >= 1 (Stopwatch-driven)
        TI -> TI: rawT = elapsed / durationMs  (clamped to [0,1])
        TI -> TI: easedT = Ease(rawT), clamped to [0,1]
        TI -> EF: InvokeUpdate(sender, args)
        TI -> FUS: Apply(target, easedT, priority)
        activate FUS
        FUS -> UI: ProtectedInvoke(target, applyCore, priority)\n(skipped if cancelled / app dead)
        UI -> FUS: applyCore: per entry → sampler.Update(target, property, start, end, options, easedT)
        FUS -> T: t<=0 → exact start / t>=1 → exact end /\nmiddle → SetValue (value) or in-place mutation (reference)
        deactivate FUS
        TI -> EF: InvokeLateUpdate(sender, args)
        TI -> TI: await Task.Delay(1)  (coarse yield only; Stopwatch is the timing source)
    end
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
deactivate TI
Sch --> TC: completed
deactivate Sch
TC --> SS
deactivate TC
SS --> User: return
deactivate SS
@enduml
```

## (b) 自动往返 / 循环流

当设置了 `IsAutoReverse` 或 `LoopTime` 时，解释器会把采样程包起来。`LoopTime = int.MaxValue` 表示无限循环。

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "SamplerSet" as FUS
participant "Effect" as EF

TI -> TI: durationMs = effect.Duration.TotalMilliseconds
TI -> TI: stopwatch = Stopwatch.StartNew()
TI -> EF: InvokeStart(sender, args)

loop loop in 0 .. effect.LoopTime (forever when int.MaxValue)
    loop forward pass (sample until rawT >= 1)
        TI -> TI: cts/Args.Handled check
        TI -> TI: rawT = stopwatch.Elapsed / durationMs
        TI -> TI: easedT = clamp(Ease(rawT), 0, 1)
        TI -> EF: InvokeUpdate
        TI -> FUS: Apply(target, easedT, priority)
        TI -> EF: InvokeLateUpdate
        TI -> TI: await Task.Delay(1)  (coarse yield)
    end
    alt effect.IsAutoReverse
        loop backward pass (sample until rawT >= 1)
            TI -> TI: cts/Args.Handled check
            TI -> TI: easedT = clamp(Ease(1 - rawT), 0, 1); endpoint easedT = 0
            TI -> EF: InvokeUpdate
            TI -> FUS: Apply(target, easedT, priority)
            TI -> EF: InvokeLateUpdate
            TI -> TI: await Task.Delay(1)  (coarse yield)
        end
    end
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
@enduml
```

## (c) 取消 / `TransitionEventArgs.Handled = true` 短路

被取消的 `cts`（来自 `Transition.Exit` 或新的互斥动画）或处理器把 `Handled` 设为 `true` 都会抛出 `OperationCanceledException`；解释器触发 `Canceled` + `Finally` 并停止。

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "TransitionEventArgs" as Args

TI -> TI: sampling loop
TI -> Args: Args.Handled read
alt Args.Handled == true  (event handler short-circuit)
    TI -> TI: throw OperationCanceledException
else cts.IsCancellationRequested (Transition.Exit / new mutual)
    TI -> TI: throw OperationCanceledException
end
TI -> EF: InvokeCancled(sender, args)
EF --> TI: Canceled event fired
TI -> EF: InvokeFinally(sender, args)
EF --> TI: Finally event fired
TI -> TI: stop immediately
@enduml
```

**应用关闭路径：** `SamplerSet.Apply` 会检查 `inspector.IsAppAlive()`（通过 `CanSetValue`）；当其为 `false`（例如 WinUI `DispatcherQueue` 入队失败）时跳过写入。`ApplyCore` 内的同一守卫会在一次采样中途停止，因此采样不再应用且不再触发更多事件。被取消的动画（`cts.IsCancellationRequested`）同样跳过已排队的写入 —— 即原 `ICancellableFrameSequence` 的过期帧守卫。

## (d) 互斥 vs 非互斥调度器扇出

一个目标**至多**持有一个共享互斥调度器（由 `SemaphoreSlim` 串行化），但可以同时持有**多个**并发的非互斥调度器。

```plantuml
@startuml
!theme plain

participant "StateSnapshot.Execute" as EX
participant "Target" as T
participant "MutualSchedulers (CWT)" as MWT
participant "NoMutualSchedulers (CWT)" as NWT
participant "Scheduler (mutual, shared)" as SA
participant "Scheduler (non-mutual #1)" as SB1
participant "Scheduler (non-mutual #2)" as SB2

EX -> MWT: CanMutualTask: true -> FindOrCreate(target)
MWT --> EX: shared scheduler (1 per target)
EX -> SA: Execute(producer, state, effect, cts)
SA -> SA: gate.WaitAsync() serializes; new mutual animation Exit()s the previous
SA -> T: apply sampler writes (UI-marshalled)

EX -> NWT: CanMutualTask: false -> AddNoMutual(target, [scheduler])
EX -> SB1: Execute(...)
EX -> SB2: Execute(...)
SB1 -> T: apply sampler writes in parallel
SB2 -> T: apply sampler writes in parallel
SB1 -> NWT: RemoveNoMutual(target, [SB1]) on Completed
SB2 -> NWT: RemoveNoMutual(target, [SB2]) on Completed
@enduml
```

## 流程汇总

| 场景 | 行为 |
|---|---|
| 正常执行 | `InterpolatorCore.Prepare` 为每个属性解析 `ISampleable` 并 `Normalize` 得到 `ISampler`（读取 current=start、target=end）；解释器用 Stopwatch 连续采样（`t = elapsed/duration`，缓动 + 钳制），并经 `SamplerSet.Apply` 编组到 UI 线程应用；每次采样触发 `Update`/`LateUpdate` 事件；结束时触发 `Completed` + `Finally`。 |
| `IsAutoReverse` | 正向程后，解释器运行反向程（复用同一批采样器；程末 `easedT` 强制为 0）。 |
| `LoopTime` / `int.MaxValue` | 整个正向（+ 反向）程重复 `LoopTime` 次，或永远。 |
| 同目标新的互斥动画 | 新运行前 `CoreExecute` 调用 `scheduler.Exit()`；先前调度器取消其当前 `cts`。 |
| `TransitionEventArgs.Handled = true` | 抛出 `OperationCanceledException` → `Canceled` + `Finally`；时间线停止。 |
| `Transition.Exit(target)` | 取消目标的互斥（可选非互斥）调度器。 |
| 后台线程启动 | `UIThreadInspector.ProtectedInvoke`/`ProtectedGetValue` 把读取与写入编组到 UI 线程。 |
| 属性无采样器 | `Prepare` 中跳过该属性（`UnreadablePath` 哨兵或未解析到 `ISampleable`）；其余属性照常动画。 |
| 应用关闭 | `SamplerSet.CanSetValue()` 检查 `IsAppAlive()` → 跳过写入，不再触发事件。 |

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs`（Stopwatch 驱动采样循环、`ExecuteSamplingLoopAsync`）、`TransitionScheduler.cs`（`FindOrCreate`、`Execute`、门控）、`Interpolator.cs`（`Prepare`、采样器解析）、`SamplerSet.cs`（`Apply`、取消/应用存活跳过）、`StateSnapshot.cs`（`CoreExecute`）、`Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`。
